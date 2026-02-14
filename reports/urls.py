from django.urls import path
from reports import views

app_name = 'reports'

urlpatterns = [
    path('payroll-register/<int:period_id>/', views.PayrollRegisterView.as_view(), name='payroll-register'),
    path('payroll-register/<int:period_id>/export/', views.PayrollRegisterExportView.as_view(), name='payroll-register-export'),
    path('contract-labour/<int:period_id>/', views.ContractLabourView.as_view(), name='contract-labour'),
    path('contract-labour/<int:period_id>/export/', views.ContractLabourExportView.as_view(), name='contract-labour-export'),
    path('contract-profitability/<int:period_id>/', views.ContractProfitabilityView.as_view(), name='contract-profitability'),
    path('contract-profitability/<int:period_id>/export/', views.ContractProfitabilityExportView.as_view(), name='contract-profitability-export'),
]
