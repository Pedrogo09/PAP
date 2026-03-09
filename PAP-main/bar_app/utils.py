from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from datetime import datetime
from django.core import signing
from django.core.mail import EmailMessage
from django.conf import settings


# token functions

def make_verification_token(user):
    """Cria token temporário para verificação de email.
    O token contém o PK do utilizador e expira em 1 dia.
    """
    signer = signing.TimestampSigner()
    return signer.sign(str(user.pk))


def check_verification_token(token, max_age=60*60*24):
    """Dessign a token e retorna o utilizador se válido, caso contrário None."""
    signer = signing.TimestampSigner()
    try:
        pk = signer.unsign(token, max_age=max_age)
        from .models import User
        return User.objects.get(pk=pk)
    except Exception:
        return None


def send_pdf_email(user, subject, body, pdf_buffer, filename):
    """Envia um email com um PDF anexo se o utilizador tiver email válido.

    Falha silenciosamente (não lança) para não bloquear operações críticas.
    """
    if not user.email or not user.email_verified:
        return

    # Substituir hífens problemáticos e garantir unicode
    def fix_unicode(text):
        if not isinstance(text, str):
            text = str(text)
        # Substitui hífen não separável e outros por hífen normal
        return text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')

    subject = fix_unicode(subject)
    body = fix_unicode(body)
    filename = fix_unicode(filename)

    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        to=[user.email],
    )
    msg.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
    try:
        msg.send(fail_silently=True)
    except Exception as e:
        # Log opcional: print(f"Erro ao enviar email: {e}")
        pass


def _build_doc_buffer(title):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    return buffer, doc


def generate_topup_pdf(transaction):
    buffer, doc = _build_doc_buffer('Comprovativo de Carregamento')
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('Header', parent=styles['Heading1'], alignment=1)
    story.append(Paragraph('Bar Escolar', header_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>Comprovativo de Carregamento</b>', styles['Title']))
    story.append(Spacer(1, 6))

    # Meta
    dt = transaction.created_at if getattr(transaction, 'created_at', None) else datetime.now()
    story.append(Paragraph(f'Data/Hora: {dt.strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    story.append(Paragraph(f'Utilizador: {transaction.user.get_full_name() or transaction.user.username}', styles['Normal']))
    story.append(Spacer(1, 12))

    # Details table
    data = [
        ['Descrição', 'Montante'],
        [transaction.description or 'Carregamento de saldo', f'€{transaction.amount:.2f}']
    ]

    t = Table(data, colWidths=[120*mm, 40*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#efefef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Footer balance
    story.append(Paragraph(f'Atual Saldo: €{transaction.user.balance:.2f}', styles['Normal']))
    story.append(Spacer(1, 24))

    story.append(Paragraph('Obrigado pela sua compra.', styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_order_pdf(order, transaction=None):
    buffer, doc = _build_doc_buffer('Recibo de Pedido')
    styles = getSampleStyleSheet()
    story = []

    header_style = ParagraphStyle('Header', parent=styles['Heading1'], alignment=1)
    story.append(Paragraph('Bar Escolar', header_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>RECIBO DE PEDIDO</b>', styles['Title']))
    story.append(Spacer(1, 2))
    
    # Linha divisória
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=1, spaceAfter=1))
    story.append(Spacer(1, 6))

    dt = order.created_at if getattr(order, 'created_at', None) else datetime.now()
    story.append(Paragraph(f'Data/Hora: {dt.strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    story.append(Paragraph(f'Pedido Nº: {order.order_number}', styles['Normal']))
    story.append(Paragraph(f'Utilizador: {order.user.get_full_name() or order.user.username}', styles['Normal']))
    story.append(Spacer(1, 12))

    # Items table header
    data = [['Quantidade', 'Produto', 'Preço Unit.', 'Subtotal']]
    for item in order.items.all():
        data.append([
            str(item.quantity),
            item.product.name,
            f'€{item.unit_price:.2f}',
            f'€{item.subtotal:.2f}'
        ])

    # Totals
    data.append(['', '', 'Total:', f'€{order.total_amount:.2f}'])

    t = Table(data, colWidths=[25*mm, 85*mm, 30*mm, 20*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#efefef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('SPAN', (0, len(data)-1), (1, len(data)-1)),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    if transaction:
        payment_label = transaction.get_transaction_type_display()
        story.append(Paragraph(f'<b>Forma de Pagamento:</b> {payment_label}', styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph('Obrigado pela sua compra.', styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer
