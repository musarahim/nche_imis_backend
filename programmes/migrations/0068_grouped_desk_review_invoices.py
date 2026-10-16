from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def preserve_existing_invoices(apps, schema_editor):
    Invoice = apps.get_model('programmes', 'ProgrammeAssessmentInvoice')
    Line = apps.get_model('programmes', 'DeskReviewInvoiceLine')
    database = schema_editor.connection.alias
    for invoice in Invoice.objects.using(database).select_related('application').iterator():
        application = invoice.application
        Line.objects.using(database).create(invoice_id=invoice.pk, application_id=application.pk,
            application_number=application.application_number, programme_name=application.programme_name,
            desk_review_fee=invoice.desk_review_fee)
        Invoice.objects.using(database).filter(pk=invoice.pk).update(institution_id=application.institution_id,
            verified_amount=invoice.grand_total if invoice.cleared and invoice.status == 'reconciled' else Decimal('0.00'))


class Migration(migrations.Migration):
    dependencies = [
        ('programmes', '0067_rename_programme_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name='programmeassessmentinvoice', name='institution',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='desk_review_invoices', to='institutions.institution')),
        migrations.AddField(model_name='programmeassessmentinvoice', name='verified_amount',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0)),
        migrations.CreateModel(name='DeskReviewInvoiceLine', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('application_number', models.CharField(max_length=100)),
            ('programme_name', models.CharField(max_length=255)),
            ('desk_review_fee', models.DecimalField(max_digits=10, decimal_places=2)),
            ('application', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                related_name='desk_review_invoice_lines', to='programmes.programaccreditation')),
            ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                related_name='lines', to='programmes.programmeassessmentinvoice')),
        ], options={'ordering': ['pk'], 'constraints': [models.UniqueConstraint(fields=('invoice', 'application'), name='unique_desk_review_invoice_programme')]}),
        migrations.CreateModel(name='DeskReviewPaymentVerification', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('verified_total', models.DecimalField(max_digits=10, decimal_places=2)),
            ('verified_at', models.DateTimeField(auto_now_add=True)),
            ('payment_reference', models.CharField(max_length=255)),
            ('payment_receipt', models.FileField(blank=True, upload_to='assessment_invoices/')),
            ('payment_date', models.DateField(blank=True, null=True)),
            ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                related_name='verifications', to='programmes.programmeassessmentinvoice')),
            ('verified_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['verified_at', 'pk']}),
        # Grouped invoices cannot be represented by the old single-application schema.
        migrations.RunPython(preserve_existing_invoices),
        migrations.RemoveField(model_name='programmeassessmentinvoice', name='application'),
        migrations.AlterField(model_name='programmeassessmentinvoice', name='institution',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                related_name='desk_review_invoices', to='institutions.institution')),
    ]
