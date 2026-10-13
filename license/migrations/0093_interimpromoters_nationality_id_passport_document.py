import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('license', '0092_universityprovisionallicense_geographical_location'),
        ('common', '0009_financeyear_nationality'),
    ]

    operations = [
        migrations.AddField(
            model_name='interimpromoters', name='nationality',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='common.nationality'),
        ),
        migrations.AddField(
            model_name='interimpromoters', name='id_passport_document',
            field=models.FileField(blank=True, null=True, upload_to='interim_promoters/identity/'),
        ),
    ]
