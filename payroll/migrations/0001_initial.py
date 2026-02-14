from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


def seed_initial_data(apps, schema_editor):
    Contract = apps.get_model('payroll', 'Contract')
    StatutorySetting = apps.get_model('payroll', 'StatutorySetting')
    NISBracket = apps.get_model('payroll', 'NISBracket')

    Contract.objects.get_or_create(
        name='Projects/Overhead',
        defaults={'active': True, 'is_internal': True, 'notes': 'Internal non-billable bucket.'},
    )
    StatutorySetting.objects.get_or_create(
        effective_date='2026-01-01',
        defaults={
            'health_surcharge_threshold_monthly': Decimal('5000.00'),
            'health_surcharge_high_weekly': Decimal('8.25'),
            'health_surcharge_low_weekly': Decimal('4.80'),
        },
    )
    NISBracket.objects.get_or_create(
        effective_date='2026-01-01',
        monthly_min=Decimal('0.00'),
        monthly_max=Decimal('3000.00'),
        defaults={
            'earnings_class': 'A',
            'employee_weekly': Decimal('20.00'),
            'employer_weekly': Decimal('30.00'),
        },
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('active', models.BooleanField(default=True)),
                ('is_internal', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
            ],
            options={'ordering': ('name',)},
        ),
        migrations.CreateModel(
            name='NISBracket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effective_date', models.DateField()),
                ('monthly_min', models.DecimalField(decimal_places=2, max_digits=12)),
                ('monthly_max', models.DecimalField(decimal_places=2, max_digits=12)),
                ('earnings_class', models.CharField(max_length=20)),
                ('employee_weekly', models.DecimalField(decimal_places=2, max_digits=10)),
                ('employer_weekly', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={'ordering': ('-effective_date', 'monthly_min')},
        ),
        migrations.CreateModel(
            name='StatutorySetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effective_date', models.DateField()),
                ('health_surcharge_threshold_monthly', models.DecimalField(decimal_places=2, max_digits=12)),
                ('health_surcharge_high_weekly', models.DecimalField(decimal_places=2, max_digits=10)),
                ('health_surcharge_low_weekly', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={'ordering': ('-effective_date',)},
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('active', models.BooleanField(default=True)),
                ('pay_type', models.CharField(choices=[('BASE_MONTHLY', 'Base Monthly'), ('CASUAL', 'Casual')], max_length=20)),
                ('base_daily_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('base_days_per_week', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('notes', models.TextField(blank=True)),
                ('default_contract', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='payroll.contract')),
            ],
            options={'ordering': ('name',)},
        ),
        migrations.CreateModel(
            name='PayPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=50, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('contribution_weeks', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('LOCKED', 'Locked')], default='DRAFT', max_length=10)),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
                ('locked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'ordering': ('-start_date',)},
        ),
        migrations.CreateModel(
            name='Overhead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('allocation_method', models.CharField(choices=[('DIRECT_TO_CONTRACT', 'Direct to Contract'), ('ALLOCATE_BY_REVENUE_SHARE', 'Allocate by Revenue Share'), ('ALLOCATE_BY_LABOUR_SHARE', 'Allocate by Labour Share')], max_length=30)),
                ('contract', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='direct_overheads', to='payroll.contract')),
                ('pay_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='overheads', to='payroll.payperiod')),
            ],
        ),
        migrations.CreateModel(
            name='PayLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pay_code', models.CharField(choices=[('BASE', 'Base'), ('DAYS', 'Days'), ('OT', 'Overtime'), ('PUBLIC_HOLIDAY', 'Public Holiday'), ('ALLOWANCE', 'Allowance'), ('OUTSIDE_JOB', 'Outside Job'), ('DEDUCTION', 'Deduction'), ('ADJUSTMENT', 'Adjustment')], max_length=20)),
                ('unit', models.CharField(choices=[('DAY', 'Day'), ('HOUR', 'Hour'), ('LUMP_SUM', 'Lump Sum')], default='LUMP_SUM', max_length=10)),
                ('qty', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pay_lines', to='payroll.contract')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pay_lines', to='payroll.employee')),
                ('pay_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pay_lines', to='payroll.payperiod')),
            ],
            options={'ordering': ('employee__name', 'id')},
        ),
        migrations.CreateModel(
            name='ContractBilling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('billing_pre_tax', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='billings', to='payroll.contract')),
                ('pay_period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billings', to='payroll.payperiod')),
            ],
            options={'ordering': ('contract__name',), 'unique_together': {('pay_period', 'contract')}},
        ),
        migrations.RunPython(seed_initial_data, migrations.RunPython.noop),
    ]
