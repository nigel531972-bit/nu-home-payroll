from django.contrib import admin
from django.urls import include, path
from payroll.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', HomeView.as_view(), name='home'),
    path('payroll/', include('payroll.urls')),
    path('reports/', include('reports.urls')),
]
