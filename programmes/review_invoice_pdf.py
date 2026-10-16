"""Shared invoice layout for email attachments and portal downloads."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def payment_details():
    # Defaults transcribed from the supplied NCHE desk review invoice.
    return getattr(settings, 'DESK_REVIEW_INVOICE_PAYMENT_DETAILS', {
        'account_name': 'National Council for Higher Education – Other Collections',
        'account_number': '9030005961989',
        'bank': 'Stanbic Bank',
        'branch': 'Kyambogo',
    })


def amount_in_words(amount):
    small = ('Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen').split()
    tens = ('Zero Ten Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety').split()

    def words(number):
        if number < 20:
            return small[number]
        if number < 100:
            return tens[number // 10] + (' ' + small[number % 10] if number % 10 else '')
        for value, label in [(1000000000, 'Billion'), (1000000, 'Million'), (1000, 'Thousand'), (100, 'Hundred')]:
            if number >= value:
                return words(number // value) + ' ' + label + (' ' + words(number % value) if number % value else '')

    whole = int(amount)
    cents = int((amount - whole) * 100)
    return words(whole) + ' Shillings' + (' and ' + words(cents) + ' Cents' if cents else '') + ' Only'


def build_review_invoice_pdf(invoice):
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=48, leftMargin=48,
        topMargin=32, bottomMargin=46, title=f'NCHE Invoice {invoice.invoice_number}')
    styles = getSampleStyleSheet()
    body = ParagraphStyle('InvoiceBody', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leading=15)
    bold = ParagraphStyle('InvoiceBold', parent=body, fontName='Times-Bold')
    centre = ParagraphStyle('InvoiceCentre', parent=bold, alignment=TA_CENTER)
    right = ParagraphStyle('InvoiceRight', parent=body, alignment=TA_RIGHT)
    def p(value, style=body):
        return Paragraph(escape(str(value)), style)

    story = []
    logo = Path(__file__).resolve().parent.parent / 'static' / 'images' / 'invoice-letterhead.png'
    if logo.exists():
        story.append(Image(str(logo), width=330, height=110))
    else:
        story.append(p('NATIONAL COUNCIL FOR HIGHER EDUCATION', centre))
    rule = Table([['']], colWidths=[499])
    rule.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), .7, colors.black)]))
    story.extend([rule, Spacer(1, 24), p('INVOICE', centre), Spacer(1, 18)])
    meta = Table([[p(f'Date: {invoice.invoice_date:%d %B, %Y}'), p(f'No. {invoice.invoice_number}', right)]], colWidths=[270, 229])
    meta.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.extend([meta, Spacer(1, 14), p('The Academic Registrar'), p(invoice.institution.name)])
    if invoice.institution.postal_address:
        story.append(p(invoice.institution.postal_address))
    story.extend([Spacer(1, 16), p('Subject: Programme Accreditation – Desk Review', bold), Spacer(1, 14)])
    rows = [[p('Description', bold), p('No.', bold), p('Total Cost (UGX)', bold)]]
    for line in invoice.lines.all():
        description = Paragraph('<b>Programme</b><br/><i>' + escape(line.programme_name)
            + '</i><br/>' + escape(line.application_number), body)
        rows.append([description, p('1', centre), p(f'{line.desk_review_fee:,.2f}', right)])
    rows.extend([
        [p('10% administrative costs'), '', p(f'{invoice.administrative_fee:,.2f}', right)],
        [p('Total', bold), '', p(f'{invoice.grand_total:,.2f}', right)],
    ])
    table = Table(rows, colWidths=[348, 36, 115], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), .6, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
    ]))
    story.extend([table, Spacer(1, 14), p(
        f'Please remit UGX {invoice.grand_total:,.2f} ({amount_in_words(invoice.grand_total)}) to the following bank account. '
        'All payments should be made through the bank. Upon confirmation of payment, an official receipt will be issued.'),
        p('Please quote the invoice number when making payments.', bold), Spacer(1, 14)])
    details = payment_details()
    for label, key in [('Account Name', 'account_name'), ('Account No.', 'account_number'), ('Bank', 'bank'), ('Branch', 'branch')]:
        story.append(p(f'{label}: {details[key]}', bold))
    story.extend([Spacer(1, 20), p('Thank you.'), Spacer(1, 14), p('For: DIRECTOR FINANCE', bold)])

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 8)
        canvas.line(48, 34, A4[0] - 48, 34)
        canvas.drawString(48, 23, f'NCHE | {invoice.invoice_number}')
        canvas.drawRightString(A4[0] - 48, 23, f'Page {doc.page}')
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
