from django.db import migrations


def copy_existing_details(apps, schema_editor):
    Appraisal = apps.get_model('appraisals', 'PerformanceAppraisal')
    Employee = apps.get_model('hr', 'Employee')
    GradeScale = apps.get_model('hr', 'GradeScale')
    for appraisal in Appraisal.objects.all().iterator():
        if appraisal.appraisee_id:
            employee = Employee.objects.get(pk=appraisal.appraisee_id)
            fields = []
            if appraisal.employment_terms and not employee.employment_terms:
                employee.employment_terms = appraisal.employment_terms
                fields.append('employment_terms')
            if appraisal.present_appointment_date and not employee.present_appointment_date:
                employee.present_appointment_date = appraisal.present_appointment_date
                fields.append('present_appointment_date')
            if appraisal.appraisee_salary_scale and not employee.grade_scale_id:
                scale = GradeScale.objects.filter(code=appraisal.appraisee_salary_scale).first()
                if scale:
                    employee.grade_scale_id = scale.pk
                    fields.append('grade_scale')
            if fields:
                employee.save(update_fields=fields)
        if appraisal.appraiser_id and appraisal.appraiser_salary_scale:
            employee = Employee.objects.get(pk=appraisal.appraiser_id)
            if not employee.grade_scale_id:
                scale = GradeScale.objects.filter(code=appraisal.appraiser_salary_scale).first()
                if scale:
                    employee.grade_scale_id = scale.pk
                    employee.save(update_fields=['grade_scale'])


class Migration(migrations.Migration):
    dependencies = [
        ('appraisals', '0006_appraisal_personal_information'),
        ('hr', '0024_employee_appraisal_biodata'),
    ]

    operations = [
        migrations.RunPython(copy_existing_details, migrations.RunPython.noop),
        migrations.RemoveField(model_name='performanceappraisal', name='employment_terms'),
        migrations.RemoveField(model_name='performanceappraisal', name='present_appointment_date'),
        migrations.RemoveField(model_name='performanceappraisal', name='appraisee_salary_scale'),
        migrations.RemoveField(model_name='performanceappraisal', name='appraiser_salary_scale'),
    ]
