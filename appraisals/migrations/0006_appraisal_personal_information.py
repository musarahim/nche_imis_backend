from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('appraisals', '0005_alter_appraisalcomment_modified_and_more')]

    operations = [
        migrations.AddField(model_name='performanceappraisal', name='employment_terms', field=models.CharField(blank=True, choices=[('probation', 'Probation'), ('contract', 'Contract'), ('temporary', 'Temporary')], max_length=20)),
        migrations.AddField(model_name='performanceappraisal', name='present_appointment_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='performanceappraisal', name='appraisee_salary_scale', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='performanceappraisal', name='appraiser_salary_scale', field=models.CharField(blank=True, max_length=100)),
    ]
