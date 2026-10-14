from django.db import migrations


def update_types(apps, schema_editor):
    applications = apps.get_model('programmes', 'ProgramAccreditation').objects.using(schema_editor.connection.alias)
    applications.filter(application_type='new').update(application_type='accredit')
    applications.filter(application_type='renewal').update(application_type='re-accredit')


def restore_types(apps, schema_editor):
    applications = apps.get_model('programmes', 'ProgramAccreditation').objects.using(schema_editor.connection.alias)
    applications.filter(application_type='accredit').update(application_type='new')
    applications.filter(application_type='re-accredit').update(application_type='renewal')


class Migration(migrations.Migration):
    dependencies = [
        ('programmes', '0065_alter_programaccreditation_application_type'),
    ]

    operations = [migrations.RunPython(update_types, restore_types)]
