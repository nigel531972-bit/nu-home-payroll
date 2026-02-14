from datetime import date
from decimal import Decimal

from django.test import TestCase

from payroll.models import Contract, ContractBilling, Employee, NISBracket, Overhead, PayLine, PayPeriod, StatutorySetting
from payroll.services import contract_profitability, generate_base_salary_lines, get_active_nis_bracket, payroll_register


class PayrollServiceTests(TestCase):
    def setUp(self):
        self.internal = Contract.objects.create(name='Projects/Overhead', is_internal=True)
        self.c1 = Contract.objects.create(name='Contract A')
        self.c2 = Contract.objects.create(name='Contract B')
        self.emp = Employee.objects.create(
            name='Alice',
            pay_type=Employee.PayType.BASE_MONTHLY,
            base_daily_rate=Decimal('150.00'),
            base_days_per_week=Decimal('5.00'),
            default_contract=self.c1,
        )
        self.period = PayPeriod.objects.create(label='Jan 2026', start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        NISBracket.objects.create(
            effective_date=date(2026, 1, 1),
            monthly_min=Decimal('0.00'),
            monthly_max=Decimal('10000.00'),
            earnings_class='A',
            employee_weekly=Decimal('30.00'),
            employer_weekly=Decimal('45.00'),
        )
        StatutorySetting.objects.create(
            effective_date=date(2026, 1, 1),
            health_surcharge_threshold_monthly=Decimal('5000.00'),
            health_surcharge_high_weekly=Decimal('8.25'),
            health_surcharge_low_weekly=Decimal('4.80'),
        )

    def test_mondays_count_january_2026(self):
        self.assertEqual(self.period.contribution_weeks, 4)

    def test_base_salary_formula(self):
        generate_base_salary_lines(self.period)
        line = PayLine.objects.get(pay_period=self.period, employee=self.emp, pay_code=PayLine.PayCode.BASE)
        self.assertEqual(line.amount, Decimal('3250.00'))

    def test_nis_bracket_lookup(self):
        bracket = get_active_nis_bracket(Decimal('2000.00'), self.period)
        self.assertIsNotNone(bracket)
        self.assertEqual(bracket.earnings_class, 'A')

    def test_health_surcharge_and_contribution_weeks(self):
        PayLine.objects.create(
            pay_period=self.period,
            employee=self.emp,
            contract=self.c1,
            pay_code=PayLine.PayCode.DAYS,
            unit=PayLine.Unit.LUMP_SUM,
            amount=Decimal('6000.00'),
        )
        row = payroll_register(self.period)[0]
        self.assertEqual(row['health_surcharge'], Decimal('33.00'))

    def test_overhead_allocation_sums_exactly(self):
        PayLine.objects.create(pay_period=self.period, employee=self.emp, contract=self.c1, pay_code=PayLine.PayCode.DAYS, amount=Decimal('1000.00'))
        PayLine.objects.create(pay_period=self.period, employee=self.emp, contract=self.c2, pay_code=PayLine.PayCode.DAYS, amount=Decimal('500.00'))
        ContractBilling.objects.create(pay_period=self.period, contract=self.c1, billing_pre_tax=Decimal('2000.00'))
        ContractBilling.objects.create(pay_period=self.period, contract=self.c2, billing_pre_tax=Decimal('1000.00'))

        Overhead.objects.create(pay_period=self.period, category='fuel', amount=Decimal('300.00'), allocation_method=Overhead.AllocationMethod.ALLOCATE_BY_REVENUE_SHARE)
        Overhead.objects.create(pay_period=self.period, category='rent', amount=Decimal('150.00'), allocation_method=Overhead.AllocationMethod.ALLOCATE_BY_LABOUR_SHARE)
        rows = contract_profitability(self.period)
        self.assertEqual(sum(r['overheads'] for r in rows), Decimal('450.00'))
