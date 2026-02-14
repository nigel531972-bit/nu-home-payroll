from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView

from payroll.forms import ContractBillingForm, ContractForm, EmployeeForm, OverheadForm, PayLineForm, PayPeriodForm
from payroll.models import Contract, ContractBilling, Employee, Overhead, PayLine, PayPeriod
from payroll.services import generate_base_salary_lines


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'


class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'payroll/contracts.html'


class ContractCreateView(LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'payroll/form.html'
    success_url = reverse_lazy('payroll:contracts')


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'payroll/employees.html'


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/form.html'
    success_url = reverse_lazy('payroll:employees')


class PayPeriodListView(LoginRequiredMixin, ListView):
    model = PayPeriod
    template_name = 'payroll/pay_periods.html'


class PayPeriodCreateView(LoginRequiredMixin, CreateView):
    model = PayPeriod
    form_class = PayPeriodForm
    template_name = 'payroll/form.html'
    success_url = reverse_lazy('payroll:pay-periods')


class PayPeriodDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'payroll/pay_period_detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.pay_period = get_object_or_404(PayPeriod, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.pay_period.status == PayPeriod.Status.LOCKED and 'lock_period' not in request.POST:
            messages.error(request, 'This period is locked.')
            return redirect('payroll:pay-period-detail', pk=self.pay_period.pk)

        if 'generate_base' in request.POST:
            created = generate_base_salary_lines(self.pay_period)
            messages.success(request, f'Generated {created} base salary lines.')
        elif 'add_payline' in request.POST:
            form = PayLineForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.pay_period = self.pay_period
                if obj.pay_code in (PayLine.PayCode.ALLOWANCE, PayLine.PayCode.OUTSIDE_JOB) and not obj.contract_id:
                    obj.contract = Contract.objects.filter(name='Projects/Overhead', is_internal=True).first()
                obj.save()
                messages.success(request, 'Pay line added.')
            else:
                messages.error(request, form.errors)
        elif 'add_billing' in request.POST:
            form = ContractBillingForm(request.POST)
            if form.is_valid():
                ContractBilling.objects.update_or_create(
                    pay_period=self.pay_period,
                    contract=form.cleaned_data['contract'],
                    defaults={'billing_pre_tax': form.cleaned_data['billing_pre_tax']},
                )
                messages.success(request, 'Billing saved.')
            else:
                messages.error(request, form.errors)
        elif 'add_overhead' in request.POST:
            form = OverheadForm(request.POST)
            if form.is_valid():
                ov = form.save(commit=False)
                ov.pay_period = self.pay_period
                ov.save()
                messages.success(request, 'Overhead saved.')
            else:
                messages.error(request, form.errors)
        elif 'lock_period' in request.POST:
            self.pay_period.lock(request.user)
            messages.success(request, 'Pay period locked.')
        return HttpResponseRedirect(reverse('payroll:pay-period-detail', kwargs={'pk': self.pay_period.pk}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_filter = self.request.GET.get('employee')
        pay_lines = self.pay_period.pay_lines.select_related('employee', 'contract')
        if employee_filter:
            pay_lines = pay_lines.filter(Q(employee__name__icontains=employee_filter))
        context.update(
            {
                'period': self.pay_period,
                'pay_lines': pay_lines,
                'payline_form': PayLineForm(),
                'billing_form': ContractBillingForm(),
                'overhead_form': OverheadForm(),
                'billings': self.pay_period.billings.select_related('contract'),
                'overheads': self.pay_period.overheads.select_related('contract'),
            }
        )
        return context
