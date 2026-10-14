from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('programmes', '0063_preliminaryreview_progression_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='programaccreditation',
            name='number_of_years',
        ),
    ]
