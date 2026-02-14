from django import forms

from payroll.models import Contract, ContractBilling, Employee, Overhead, PayLine, PayPeriod


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['name', 'active', 'is_internal', 'notes']


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'name',
            'active',
            'pay_type',
            'base_daily_rate',
            'base_days_per_week',
            'default_contract',
            'notes',
        ]


class PayPeriodForm(forms.ModelForm):
    class Meta:
        model = PayPeriod
        fields = ['label', 'start_date', 'end_date', 'contribution_weeks']


class PayLineForm(forms.ModelForm):
    class Meta:
        model = PayLine
        fields = ['employee', 'contract', 'pay_code', 'unit', 'qty', 'rate', 'amount', 'notes']


class ContractBillingForm(forms.ModelForm):
    class Meta:
        model = ContractBilling
        fields = ['contract', 'billing_pre_tax']


class OverheadForm(forms.ModelForm):
    class Meta:
        model = Overhead
        fields = ['category', 'amount', 'allocation_method', 'contract']
