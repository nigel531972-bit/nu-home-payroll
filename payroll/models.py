from calendar import monthcalendar
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Contract(models.Model):
    name = models.CharField(max_length=150, unique=True)
    active = models.BooleanField(default=True)
    is_internal = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Employee(models.Model):
    class PayType(models.TextChoices):
        BASE_MONTHLY = 'BASE_MONTHLY', 'Base Monthly'
        CASUAL = 'CASUAL', 'Casual'

    name = models.CharField(max_length=150)
    active = models.BooleanField(default=True)
    pay_type = models.CharField(max_length=20, choices=PayType.choices)
    base_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    base_days_per_week = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    default_contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='employees')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class PayPeriod(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        LOCKED = 'LOCKED', 'Locked'

    label = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    contribution_weeks = models.PositiveSmallIntegerField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    locked_at = models.DateTimeField(blank=True, null=True)
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ('-start_date',)

    def __str__(self):
        return self.label

    @staticmethod
    def mondays_in_month(any_date: date) -> int:
        weeks = monthcalendar(any_date.year, any_date.month)
        return sum(1 for week in weeks if week[0] != 0)

    def save(self, *args, **kwargs):
        if self.contribution_weeks is None and self.start_date:
            self.contribution_weeks = self.mondays_in_month(self.start_date)
        super().save(*args, **kwargs)

    def lock(self, user):
        self.status = self.Status.LOCKED
        self.locked_at = timezone.now()
        self.locked_by = user
        self.save(update_fields=['status', 'locked_at', 'locked_by'])


class PayLine(models.Model):
    class PayCode(models.TextChoices):
        BASE = 'BASE', 'Base'
        DAYS = 'DAYS', 'Days'
        OT = 'OT', 'Overtime'
        PUBLIC_HOLIDAY = 'PUBLIC_HOLIDAY', 'Public Holiday'
        ALLOWANCE = 'ALLOWANCE', 'Allowance'
        OUTSIDE_JOB = 'OUTSIDE_JOB', 'Outside Job'
        DEDUCTION = 'DEDUCTION', 'Deduction'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'

    class Unit(models.TextChoices):
        DAY = 'DAY', 'Day'
        HOUR = 'HOUR', 'Hour'
        LUMP_SUM = 'LUMP_SUM', 'Lump Sum'

    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='pay_lines')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='pay_lines')
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='pay_lines')
    pay_code = models.CharField(max_length=20, choices=PayCode.choices)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.LUMP_SUM)
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('employee__name', 'id')

    def clean(self):
        if self.pay_period_id and self.pay_period.status == PayPeriod.Status.LOCKED:
            raise ValidationError('Cannot modify pay lines in a locked period.')
        if self.pay_code in (self.PayCode.ALLOWANCE, self.PayCode.OUTSIDE_JOB):
            internal_contract = Contract.objects.filter(is_internal=True, name='Projects/Overhead').first()
            if internal_contract and not self.contract_id:
                self.contract = internal_contract
        if self.pay_code == self.PayCode.DEDUCTION and self.amount > 0:
            raise ValidationError('Deduction pay lines must be negative.')

    def save(self, *args, **kwargs):
        if self.amount is None:
            if self.unit == self.Unit.LUMP_SUM:
                self.amount = self.rate or Decimal('0.00')
            else:
                self.amount = (self.qty or Decimal('0.00')) * (self.rate or Decimal('0.00'))
        if self.pay_code in (self.PayCode.ALLOWANCE, self.PayCode.OUTSIDE_JOB) and not self.contract_id:
            internal_contract = Contract.objects.filter(is_internal=True, name='Projects/Overhead').first()
            if internal_contract:
                self.contract = internal_contract
        self.full_clean()
        super().save(*args, **kwargs)


class ContractBilling(models.Model):
    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='billings')
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='billings')
    billing_pre_tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ('pay_period', 'contract')
        ordering = ('contract__name',)


class Overhead(models.Model):
    class AllocationMethod(models.TextChoices):
        DIRECT_TO_CONTRACT = 'DIRECT_TO_CONTRACT', 'Direct to Contract'
        ALLOCATE_BY_REVENUE_SHARE = 'ALLOCATE_BY_REVENUE_SHARE', 'Allocate by Revenue Share'
        ALLOCATE_BY_LABOUR_SHARE = 'ALLOCATE_BY_LABOUR_SHARE', 'Allocate by Labour Share'

    pay_period = models.ForeignKey(PayPeriod, on_delete=models.CASCADE, related_name='overheads')
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    allocation_method = models.CharField(max_length=30, choices=AllocationMethod.choices)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, null=True, blank=True, related_name='direct_overheads')

    def clean(self):
        if self.allocation_method == self.AllocationMethod.DIRECT_TO_CONTRACT and not self.contract_id:
            raise ValidationError('Contract is required for direct overhead allocation.')


class NISBracket(models.Model):
    effective_date = models.DateField()
    monthly_min = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_max = models.DecimalField(max_digits=12, decimal_places=2)
    earnings_class = models.CharField(max_length=20)
    employee_weekly = models.DecimalField(max_digits=10, decimal_places=2)
    employer_weekly = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ('-effective_date', 'monthly_min')


class StatutorySetting(models.Model):
    effective_date = models.DateField()
    health_surcharge_threshold_monthly = models.DecimalField(max_digits=12, decimal_places=2)
    health_surcharge_high_weekly = models.DecimalField(max_digits=10, decimal_places=2)
    health_surcharge_low_weekly = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ('-effective_date',)


def pay_period_labour_totals(pay_period: PayPeriod):
    return (
        pay_period.pay_lines.values('contract_id', 'contract__name')
        .annotate(labour=Sum('amount'))
        .order_by('contract__name')
    )
