from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from reportlab.lib.units import mm
import os
from datetime import datetime
from django.core import signing
from django.core.mail import EmailMessage
from django.conf import settings
import qrcode
import base64


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


def _add_pdf_header(story, title, sub_info=None):
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle', 
        parent=styles['Heading1'], 
        alignment=0, # Left
        textColor=colors.HexColor('#6B4423'),
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=1
    )
    
    sub_style = ParagraphStyle(
        'SubInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        alignment=0,
        leading=11
    )

    # Header Table: Logo (Left) | Info (Right)
    header_data = []
    header_info = [Paragraph(title, title_style)]
    if sub_info:
        for info in sub_info:
            header_info.append(Paragraph(info, sub_style))
    
    if os.path.exists(logo_path):
        try:
            img = RLImage(logo_path, width=25*mm, height=25*mm)
            header_data = [[img, header_info]]
        except Exception:
            header_data = [[None, header_info]]
    else:
        header_data = [[None, header_info]]

    header_table = Table(header_data, colWidths=[30*mm, 140*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#6B4423'), spaceBefore=1, spaceAfter=4*mm))
    return story

def generate_topup_pdf(transaction):
    buffer, doc = _build_doc_buffer('Comprovativo de Carregamento')
    styles = getSampleStyleSheet()
    story = []

    dt = transaction.created_at if getattr(transaction, 'created_at', None) else datetime.now()
    sub_info = [
        f'Data: {dt.strftime("%d/%m/%Y %H:%M:%S")}',
        f'Utilizador: {transaction.user.get_full_name() or transaction.user.username}',
        f'Tipo: Carregamento de Saldo'
    ]

    _add_pdf_header(story, 'Comprovativo', sub_info)

    # Details table
    data = [
        ['Descrição', 'Montante'],
        [transaction.description or 'Carregamento de saldo via Terminal', f'€{transaction.amount:.2f}']
    ]

    t = Table(data, colWidths=[110*mm, 50*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B4423')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    # Total Box
    total_data = [['Saldo Final Atualizado:', f'€{transaction.user.balance:.2f}']]
    total_table = Table(total_data, colWidths=[110*mm, 50*mm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#6B4423')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 10*mm))

    # PAID Stamp look
    stamp_style = ParagraphStyle('Stamp', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#28a745'), fontName='Helvetica-Bold', alignment=1)
    story.append(Paragraph('CONFIRMADO / PAGO', stamp_style))
    story.append(Spacer(1, 10*mm))

    footer_style = ParagraphStyle('Footer', parent=styles['Italic'], alignment=1, textColor=colors.gray, fontSize=8)
    story.append(Paragraph('Este documento serve apenas como comprovativo de transação interna.', footer_style))
    story.append(Paragraph('Bar Escolar - Sistema de Gestão PAP', footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_order_pdf(order, transaction=None):
    buffer, doc = _build_doc_buffer('Recibo de Pedido')
    styles = getSampleStyleSheet()
    story = []

    dt = order.created_at if getattr(order, 'created_at', None) else datetime.now()
    sub_info = [
        f'Recibo Nº: {order.order_number}',
        f'Data: {dt.strftime("%d/%m/%Y %H:%M:%S")}',
        f'Cliente: {order.user.get_full_name() or order.user.username}'
    ]

    _add_pdf_header(story, 'RECIBO DE PEDIDO', sub_info)

    # Items table
    data = [['Qtd', 'Produto', 'P. Unitário', 'Subtotal']]
    for item in order.items.all():
        data.append([
            str(item.quantity),
            item.product.name,
            f'€{item.unit_price:.2f}',
            f'€{item.subtotal:.2f}'
        ])

    t = Table(data, colWidths=[15*mm, 90*mm, 30*mm, 30*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B4423')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.2, colors.HexColor('#eeeeee')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(t)
    
    # Total line
    total_data = [['', '', 'TOTAL:', f'€{order.total_amount:.2f}']]
    total_table = Table(total_data, colWidths=[15*mm, 90*mm, 30*mm, 30*mm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
        ('FONTNAME', (2, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (3, 0), 12),
        ('TEXTCOLOR', (2, 0), (3, 0), colors.HexColor('#6B4423')),
        ('LINEABOVE', (2, 0), (3, 0), 1, colors.HexColor('#6B4423')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 5*mm))

    if transaction:
        payment_style = ParagraphStyle('Payment', parent=styles['Normal'], fontSize=9, textColor=colors.black)
        payment_label = transaction.get_transaction_type_display()
        story.append(Paragraph(f'<b>Forma de Pagamento:</b> {payment_label}', payment_style))
    
    story.append(Spacer(1, 10*mm))
    
    # Status Stamp
    stamp_style = ParagraphStyle('Stamp', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#28a745'), fontName='Helvetica-Bold', alignment=1)
    story.append(Paragraph('PEDIDO PAGO E CONFIRMADO', stamp_style))
    story.append(Spacer(1, 10*mm))

    footer_style = ParagraphStyle('Footer', parent=styles['Italic'], alignment=1, textColor=colors.gray, fontSize=8)
    story.append(Paragraph('Obrigado pela sua preferência!', footer_style))
    story.append(Paragraph('Documento processado por computador - Bar Escolar', footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_qr_code_svg(token):
    """Gera QR Code como PNG base64 para o token do pedido"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"ORDER_TOKEN:{token}")
    qr.make(fit=True)
    
    # Gerar como PNG
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Converter para base64 para embedding em HTML
    img_base64 = base64.b64encode(buffer.read()).decode()
    return f"data:image/png;base64,{img_base64}"
