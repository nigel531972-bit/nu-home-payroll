from django.contrib import admin

from payroll.models import Contract, ContractBilling, Employee, NISBracket, Overhead, PayLine, PayPeriod, StatutorySetting

admin.site.register(Contract)
admin.site.register(Employee)
admin.site.register(PayPeriod)
admin.site.register(PayLine)
admin.site.register(ContractBilling)
admin.site.register(Overhead)
admin.site.register(NISBracket)
admin.site.register(StatutorySetting)
