import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('license', '0095_remove_universityprovisionallicense_specific_objectives_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UniversityProvisionalLicenseVehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('make', models.CharField(max_length=255)),
                ('registration_number', models.CharField(max_length=50)),
                ('university_provisional_license', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vehicles', to='license.universityprovisionallicense',
                )),
            ],
            options={'ordering': ['id']},
        ),
    ]
