from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('programmes', '0066_update_application_type_values'),
    ]

    operations = [
        migrations.RenameField(
            model_name='programaccreditation',
            old_name='program_name',
            new_name='programme_name',
        ),
        migrations.RenameField(
            model_name='program',
            old_name='program_name',
            new_name='programme_name',
        ),
    ]
