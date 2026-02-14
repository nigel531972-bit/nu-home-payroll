from django.urls import path

from payroll import views

app_name = 'payroll'

urlpatterns = [
    path('contracts/', views.ContractListView.as_view(), name='contracts'),
    path('contracts/new/', views.ContractCreateView.as_view(), name='contract-create'),
    path('employees/', views.EmployeeListView.as_view(), name='employees'),
    path('employees/new/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('periods/', views.PayPeriodListView.as_view(), name='pay-periods'),
    path('periods/new/', views.PayPeriodCreateView.as_view(), name='pay-period-create'),
    path('periods/<int:pk>/', views.PayPeriodDetailView.as_view(), name='pay-period-detail'),
]
