from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programmes', '0061_remove_programmeassessment_course_objectives'),
    ]

    operations = [
        migrations.AddField(
            model_name='programaccreditation',
            name='decision_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='programaccreditation',
            name='approved_expiry_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='programaccreditation',
            name='previous_accreditation_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='programaccreditation',
            name='previous_expiry_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
