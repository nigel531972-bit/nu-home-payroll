from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum

from payroll.models import Contract, Employee, NISBracket, Overhead, PayLine, PayPeriod, StatutorySetting


def quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_active_nis_bracket(gross_monthly: Decimal, period: PayPeriod) -> NISBracket | None:
    return (
        NISBracket.objects.filter(effective_date__lte=period.end_date, monthly_min__lte=gross_monthly, monthly_max__gte=gross_monthly)
        .order_by('-effective_date', 'monthly_min')
        .first()
    )


def get_statutory_setting(period: PayPeriod) -> StatutorySetting | None:
    return StatutorySetting.objects.filter(effective_date__lte=period.end_date).order_by('-effective_date').first()


def payroll_register(period: PayPeriod):
    rows = []
    setting = get_statutory_setting(period)
    for employee in Employee.objects.filter(active=True).order_by('name'):
        gross = period.pay_lines.filter(employee=employee).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        bracket = get_active_nis_bracket(gross, period) if gross else None
        employee_nis = (bracket.employee_weekly * period.contribution_weeks) if bracket else Decimal('0.00')
        employer_nis = (bracket.employer_weekly * period.contribution_weeks) if bracket else Decimal('0.00')
        if setting:
            weekly_hs = setting.health_surcharge_high_weekly if gross > setting.health_surcharge_threshold_monthly else setting.health_surcharge_low_weekly
        else:
            weekly_hs = Decimal('0.00')
        health = weekly_hs * period.contribution_weeks
        deductions = employee_nis + health
        net = gross - deductions
        employer_cost = gross + employer_nis
        rows.append(
            {
                'employee': employee,
                'gross': quantize(gross),
                'employee_nis': quantize(employee_nis),
                'employer_nis': quantize(employer_nis),
                'health_surcharge': quantize(health),
                'deductions': quantize(deductions),
                'net_pay': quantize(net),
                'employer_cost': quantize(employer_cost),
            }
        )
    return rows


def generate_base_salary_lines(period: PayPeriod):
    created = 0
    for employee in Employee.objects.filter(active=True, pay_type=Employee.PayType.BASE_MONTHLY):
        amount = quantize(employee.base_daily_rate * employee.base_days_per_week * Decimal('52') / Decimal('12'))
        PayLine.objects.update_or_create(
            pay_period=period,
            employee=employee,
            pay_code=PayLine.PayCode.BASE,
            defaults={
                'contract': employee.default_contract,
                'unit': PayLine.Unit.LUMP_SUM,
                'qty': None,
                'rate': amount,
                'amount': amount,
                'notes': 'Auto-generated base salary line',
            },
        )
        created += 1
    return created


def contract_labour(period: PayPeriod):
    totals = (
        period.pay_lines.values('contract_id', 'contract__name', 'contract__is_internal')
        .annotate(labour=Sum('amount'))
        .order_by('contract__name')
    )
    return [{
        'contract_id': row['contract_id'],
        'contract_name': row['contract__name'],
        'is_internal': row['contract__is_internal'],
        'labour': quantize(row['labour'] or Decimal('0.00')),
    } for row in totals]


def _distribute(total: Decimal, basis: dict[int, Decimal]) -> dict[int, Decimal]:
    sum_basis = sum(basis.values())
    if not sum_basis:
        return {k: Decimal('0.00') for k in basis}
    allocations = {}
    running = Decimal('0.00')
    ids = list(basis.keys())
    for index, contract_id in enumerate(ids):
        if index == len(ids) - 1:
            amount = total - running
        else:
            amount = quantize(total * basis[contract_id] / sum_basis)
            running += amount
        allocations[contract_id] = amount
    return allocations


def contract_profitability(period: PayPeriod):
    contracts = list(Contract.objects.filter(active=True).order_by('name'))
    labour_map = {row['contract_id']: row['labour'] for row in contract_labour(period)}
    billing_map = {b.contract_id: b.billing_pre_tax for b in period.billings.select_related('contract')}

    overhead_map = {c.id: Decimal('0.00') for c in contracts}
    for overhead in period.overheads.select_related('contract'):
        if overhead.allocation_method == Overhead.AllocationMethod.DIRECT_TO_CONTRACT:
            overhead_map[overhead.contract_id] += overhead.amount
        elif overhead.allocation_method == Overhead.AllocationMethod.ALLOCATE_BY_REVENUE_SHARE:
            basis = {c.id: billing_map.get(c.id, Decimal('0.00')) for c in contracts if not c.is_internal}
            distributed = _distribute(overhead.amount, basis)
            for cid, val in distributed.items():
                overhead_map[cid] += val
        else:
            basis = {c.id: labour_map.get(c.id, Decimal('0.00')) for c in contracts if not c.is_internal}
            distributed = _distribute(overhead.amount, basis)
            for cid, val in distributed.items():
                overhead_map[cid] += val

    rows = []
    for contract in contracts:
        billing = quantize(billing_map.get(contract.id, Decimal('0.00')))
        labour = quantize(labour_map.get(contract.id, Decimal('0.00')))
        overheads = quantize(overhead_map.get(contract.id, Decimal('0.00')))
        gross_profit = quantize(billing - labour)
        net_profit = quantize(billing - labour - overheads)
        rows.append({
            'contract': contract,
            'billing': billing,
            'labour': labour,
            'overheads': overheads,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
        })
    return rows
