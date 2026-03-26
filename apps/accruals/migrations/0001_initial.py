from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leaves', '0001_initial'),  # This assumes the first migration of 'leaves' app is '0001_initial'
    ]

    operations = [
        migrations.CreateModel(
            name='LeavePolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employment_type', models.CharField(choices=[('full_time', 'Full-time'), ('part_time', 'Part-time'), ('contractor', 'Contractor')], max_length=20)),
                ('days_per_month', models.DecimalField(decimal_places=2, max_digits=4)),
                ('max_balance', models.DecimalField(decimal_places=2, max_digits=5)),
                ('carry_forward_max', models.DecimalField(decimal_places=2, max_digits=5)),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='policies', to='leaves.leavetype')),
            ],
        ),
        migrations.CreateModel(
            name='LeaveBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=6)),
                ('year', models.IntegerField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_balances', to=settings.AUTH_USER_MODEL)),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='balances', to='leaves.leavetype')),
            ],
            options={
                'unique_together': {('employee', 'leave_type', 'year')},
            },
        ),
        migrations.CreateModel(
            name='BalanceAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('accrual', 'Accrual'), ('deduction', 'Deduction'), ('adjustment', 'Adjustment'), ('carry_forward', 'Carry Forward')], max_length=20)),
                ('delta', models.DecimalField(decimal_places=2, max_digits=5)),
                ('balance_after', models.DecimalField(decimal_places=2, max_digits=6)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('balance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='accruals.leavebalance')),
                ('performed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
