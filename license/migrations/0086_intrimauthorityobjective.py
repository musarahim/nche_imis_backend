import django.db.models.deletion
from django.db import migrations, models


def forward_copy_objectives(apps, schema_editor):
    IntrimAuthority = apps.get_model('license', 'IntrimAuthority')
    IntrimAuthorityObjective = apps.get_model('license', 'IntrimAuthorityObjective')

    rows = []
    for application in IntrimAuthority.objects.all().iterator():
        text = (application.objectives or '').strip()
        if not text:
            continue

        objectives = [line.strip() for line in text.splitlines() if line.strip()][:5]
        for index, objective in enumerate(objectives, start=1):
            rows.append(
                IntrimAuthorityObjective(
                    application_id=application.id,
                    objective=objective,
                    order=index,
                )
            )

    if rows:
        IntrimAuthorityObjective.objects.bulk_create(rows)


def reverse_copy_objectives(apps, schema_editor):
    IntrimAuthorityObjective = apps.get_model('license', 'IntrimAuthorityObjective')
    IntrimAuthorityObjective.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('license', '0085_remove_intrimauthority_names_of_promoters'),
    ]

    operations = [
        migrations.CreateModel(
            name='IntrimAuthorityObjective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('objective', models.TextField()),
                ('order', models.PositiveSmallIntegerField(default=1)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objective_items', to='license.intrimauthority')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.RunPython(forward_copy_objectives, reverse_copy_objectives),
    ]
