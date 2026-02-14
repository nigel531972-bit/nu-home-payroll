from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from payroll.models import PayPeriod
from payroll.services import contract_labour, contract_profitability, payroll_register
from reports.exports import workbook_response


class PayrollRegisterView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/payroll_register.html'

    def get_context_data(self, **kwargs):
        period = get_object_or_404(PayPeriod, pk=self.kwargs['period_id'])
        return {'period': period, 'rows': payroll_register(period)}


class PayrollRegisterExportView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        period = get_object_or_404(PayPeriod, pk=self.kwargs['period_id'])
        rows = payroll_register(period)
        data = [[r['employee'].name, r['gross'], r['employee_nis'], r['health_surcharge'], r['deductions'], r['net_pay'], r['employer_nis'], r['employer_cost']] for r in rows]
        return workbook_response(f'Payroll_Register_{period.label}.xlsx', ['Employee', 'Gross', 'NIS Employee', 'Health Surcharge', 'Deductions', 'Net Pay', 'NIS Employer', 'Employer Cost'], data)


class ContractLabourView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/contract_labour.html'

    def get_context_data(self, **kwargs):
        period = get_object_or_404(PayPeriod, pk=self.kwargs['period_id'])
        return {'period': period, 'rows': contract_labour(period)}


class ContractLabourExportView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        period = get_object_or_404(PayPeriod, pk=self.kwargs['period_id'])
        rows = contract_labour(period)
        data = [[r['contract_name'], r['labour']] for r in rows]
        return workbook_response(f'Contract_Labour_{period.label}.xlsx', ['Contract', 'Labour'], data)


class ContractProfitabilityView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/contract_profitability.html'

    def get_context_data(self, **kwargs):
        period = get_object_or_404(PayPeriod, pk=self.kwargs['period_id'])
        return {'period': period, 'rows': contract_profitability(period)}


class ContractProfitabilityExportView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        period = get_object_or_404(PayPeriod, pk=self.kwargs['period_id'])
        rows = contract_profitability(period)
        data = [[r['contract'].name, r['billing'], r['labour'], r['overheads'], r['gross_profit'], r['net_profit']] for r in rows]
        return workbook_response(f'Contract_Profitability_{period.label}.xlsx', ['Contract', 'Billing', 'Labour', 'Overheads', 'Gross Profit Before Overheads', 'Net Profit'], data)
