from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('hr', '0023_alter_department_modified_alter_dependent_modified_and_more')]

    operations = [
        migrations.AddField(model_name='employee', name='present_appointment_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='employee', name='employment_terms', field=models.CharField(blank=True, choices=[('probation', 'Probation'), ('contract', 'Contract'), ('temporary', 'Temporary')], max_length=20)),
        migrations.AddField(model_name='employee', name='grade_scale', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.gradescale')),
    ]
