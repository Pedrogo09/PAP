from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, date
import calendar
import csv
from django.http import HttpResponse
from django.db.models.functions import TruncMonth
from django.db import transaction
import io
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from ..models import (
    User, Product, Category, Order, OrderItem,
    Transaction, StockMovement, OrderReview,
    WeekdayAvailability, SchoolAccount, SchoolTransaction
)
from ..forms import AddStockForm
from .auth import is_staff_user

@login_required
@user_passes_test(is_staff_user)
def dashboard(request):
    """Painel administrativo"""
    today = timezone.localtime().date()
    total_orders_today = Order.objects.filter(scheduled_date=today).count()
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    low_stock_products = Product.objects.filter(stock__lte=F('min_stock')).count()
    critical_stock = Product.objects.filter(stock__lte=F('min_stock')).order_by('stock')[:5]
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    top_products = Product.objects.annotate(total_sold=Sum('orderitem__quantity')).order_by('-total_sold')[:5]
    
    period = request.GET.get('period', '7days')
    last_7_days = []
    sales_by_day = []
    revenue_by_day = []
    
    revenue_today = Order.objects.filter(scheduled_date=today, status__in=['ready', 'delivered', 'completed']).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    aov_today = revenue_today / total_orders_today if total_orders_today > 0 else Decimal('0.00')

    all_products = Product.objects.filter(is_available=True).select_related('category')
    # Valor gasto em stock (Preço de custo)
    # Se purchase_price estiver definido, usa-o. Caso contrário, estima 50% do preço de venda.
    total_stock_cost = sum((p.stock * (p.purchase_price if p.purchase_price is not None else (p.price * Decimal('0.50')))) for p in all_products)
    if isinstance(total_stock_cost, int):  # ensure Decimal
        total_stock_cost = Decimal(total_stock_cost)
    potential_revenue = sum((p.stock * p.price) for p in all_products)
    if isinstance(potential_revenue, int):
        potential_revenue = Decimal(potential_revenue)
    potential_profit = potential_revenue - total_stock_cost

    # Valor TOTAL gasto ao comprar stock (Histórico de despesas)
    total_spent_on_stock = SchoolTransaction.objects.filter(movement_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')


    
    if period == 'best':
        best_month_data = Order.objects.filter(status__in=['ready', 'delivered', 'completed']).annotate(
            month=TruncMonth('scheduled_date')
        ).values('month').annotate(total=Count('id')).order_by('-total').first()
        if best_month_data and best_month_data['month']:
            bm = best_month_data['month']
            _, num_days = calendar.monthrange(bm.year, bm.month)
            for d in range(1, num_days + 1):
                day_date = bm.replace(day=d)
                orders_qs = Order.objects.filter(scheduled_date=day_date, status__in=['ready', 'delivered', 'completed'])
                count = orders_qs.count()
                revenue = orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
                last_7_days.append(f"{d}/{bm.month:02d}")
                sales_by_day.append(count)
                revenue_by_day.append(float(revenue))
        else:
            last_7_days, sales_by_day, revenue_by_day = [today.strftime('%d/%m')], [0], [0.0]
    elif period == '30days':
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            orders_qs = Order.objects.filter(scheduled_date=day, status__in=['ready', 'delivered', 'completed'])
            count = orders_qs.count()
            revenue = orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            last_7_days.append(day.strftime('%d/%m'))
            sales_by_day.append(count)
            revenue_by_day.append(float(revenue))
    else:
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_name = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom'][day.weekday()]
            orders_qs = Order.objects.filter(scheduled_date=day, status__in=['ready', 'delivered', 'completed'])
            count = orders_qs.count()
            revenue = orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            last_7_days.append(f"{day_name} {day.strftime('%d/%m')}")
            sales_by_day.append(count)
            revenue_by_day.append(float(revenue))
    
    top_product_names = [p.name[:15] for p in top_products]
    top_product_quantities = [p.total_sold or 0 for p in top_products]
    school_account = SchoolAccount.objects.get(pk=1)
    
    # Previsão de Compras (Stock Predictor)
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # Incluir encomendas Pendentes e Confirmadas (representam consumo futuro planeado)
    active_statuses = ['pending', 'confirmed', 'ready', 'delivered', 'completed']
    
    sold_last_30_days = OrderItem.objects.filter(
        order__scheduled_date__gte=thirty_days_ago,
        order__status__in=active_statuses
    ).values('product_id').annotate(total_sold=Sum('quantity'))
    
    sold_last_7_days = OrderItem.objects.filter(
        order__scheduled_date__gte=seven_days_ago,
        order__status__in=active_statuses
    ).values('product_id').annotate(total_sold=Sum('quantity'))
    
    sold_dict_30 = {item['product_id']: item['total_sold'] or 0 for item in sold_last_30_days}
    sold_dict_7 = {item['product_id']: item['total_sold'] or 0 for item in sold_last_7_days}
    
    buy_suggestions = []
    total_investment_needed = Decimal('0.00')
    for p in all_products:
        # Calcular média diária nos últimos 30 dias e nos últimos 7 dias
        # Usamos float para não dar zero em divisões inteiras
        avg_30 = float(sold_dict_30.get(p.id, 0)) / 30.0
        avg_7 = float(sold_dict_7.get(p.id, 0)) / 7.0
        
        # Pega a maior média (sensibilidade a picos) ou assume um mínimo de 0.5 por dia se houver stock baixo
        daily_avg = max(avg_30, avg_7)
        
        # Previsão para os próximos 7 dias
        predicted_7d = int(round(daily_avg * 7))
        
        # Stock Alvo: Previsão + Stock Mínimo + Margem de 20%
        target_stock = int(predicted_7d * 1.2) + p.min_stock
        
        # TRIGGER: Se o stock atual for menor que o alvo OU menor que o mínimo OU perto do mínimo (margem 20%)
        if p.stock < target_stock or p.stock <= (p.min_stock * 1.2):
            suggested_buy = target_stock - p.stock
            
            # Garantir que a sugestão é pelo menos 20 unidades para teste
            if suggested_buy < 20:
                suggested_buy = 20 
                
            if suggested_buy > 0:
                p_cost = p.purchase_price if p.purchase_price is not None else (p.price * Decimal('0.50'))
                estimated_cost = Decimal(suggested_buy) * p_cost
                buy_suggestions.append({
                    'product': p,
                    'current_stock': p.stock,
                    'predicted_7d': max(predicted_7d, 1),
                    'suggested_buy': suggested_buy,
                    'estimated_cost': estimated_cost
                })
    
    # Ordenar por maior quantidade sugerida e limitar a 10
    buy_suggestions.sort(key=lambda x: x['suggested_buy'], reverse=True)
    buy_suggestions = buy_suggestions[:10]
    
    for suggestion in buy_suggestions:
        total_investment_needed += suggestion['estimated_cost']
    
    # Dados para o novo gráfico de Previsão de Stock
    stock_prediction_labels = [s['product'].name for s in buy_suggestions[:10]]
    stock_prediction_current = [s['current_stock'] for s in buy_suggestions[:10]]
    stock_prediction_needed = [s['suggested_buy'] for s in buy_suggestions[:10]]

    context = {
        'total_orders_today': total_orders_today, 'pending_orders': pending_orders,
        'low_stock_products': low_stock_products, 'critical_stock': critical_stock,
        'recent_orders': recent_orders, 'top_products': top_products,
        'last_7_days': json.dumps(last_7_days), 
        'sales_by_day': json.dumps(sales_by_day),
        'revenue_by_day': json.dumps(revenue_by_day), 
        'revenue_today': f"{Decimal(str(revenue_today)).quantize(Decimal('0.01'))}".replace('.', ','),
        'top_product_names': json.dumps(top_product_names), 
        'top_product_quantities': json.dumps(top_product_quantities),
        'stock_prediction_labels': json.dumps(stock_prediction_labels),
        'stock_prediction_current': json.dumps(stock_prediction_current),
        'stock_prediction_needed': json.dumps(stock_prediction_needed),
        'school_balance': f"{school_account.balance}".replace('.', ','),
        'selected_period': period,
        'buy_suggestions': buy_suggestions,
        'total_stock_cost': f"{total_stock_cost.quantize(Decimal('0.01'))}".replace('.', ','),
        'potential_revenue': f"{potential_revenue.quantize(Decimal('0.01'))}".replace('.', ','),
        'potential_profit': f"{potential_profit.quantize(Decimal('0.01'))}".replace('.', ','),
        'aov_today': f"{aov_today.quantize(Decimal('0.01'))}".replace('.', ','),
        'total_spent_on_stock': f"{total_spent_on_stock.quantize(Decimal('0.01'))}".replace('.', ','),
        'total_investment_needed': f"{total_investment_needed.quantize(Decimal('0.01'))}".replace('.', ','),
    }
    return render(request, 'bar_app/dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def manage_products(request):
    """Gestão de produtos"""
    products = Product.objects.all().order_by('name')
    categories = Category.objects.filter(is_active=True)
    return render(request, 'bar_app/dashboard/products.html', {
        'products': products,
        'categories': categories
    })

@login_required
@user_passes_test(is_staff_user)
def edit_product(request, pk):
    """Editar um produto via modal/POST"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produto "{product.name}" atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar produto. Verifique os dados.')
    return redirect('bar_app:manage_products')

@login_required
@user_passes_test(is_staff_user)
def manage_orders(request):
    """Gestão de pedidos"""
    status_filter = request.GET.get('status')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'bar_app/dashboard/orders.html', {'orders': orders, 'status_filter': status_filter})

@login_required
@user_passes_test(is_staff_user)
def update_order_status(request, pk):
    """Atualizar status de um pedido"""
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Pedido {order.order_number} atualizado para {order.get_status_display()}.')
        else:
            messages.error(request, 'Status inválido.')
    return redirect('bar_app:manage_orders')

@login_required
@user_passes_test(is_staff_user)
def manage_stock(request):
    """Gestão de stock"""
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')
    all_products = Product.objects.all()
    recent_movements = StockMovement.objects.all()[:20]
    return render(request, 'bar_app/dashboard/stock.html', {
        'products': all_products, 'low_stock_products': low_stock_products, 'recent_movements': recent_movements
    })

@login_required
@user_passes_test(is_staff_user)
@transaction.atomic
def replenish_stock(request, product_id):
    """Repor stock de um produto"""
    product = get_object_or_404(Product.objects.select_for_update(), pk=product_id)
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        try:
            quantity = int(quantity)
            if quantity > 0:
                product.stock += quantity
                product.save()
                StockMovement.objects.create(
                    product=product, movement_type='in', quantity=quantity,
                    reason='Reposição manual de stock', created_by=request.user
                )
                messages.success(request, f'Stock de {product.name} aumentado em {quantity} unidades.')
            else:
                messages.error(request, 'Quantidade inválida.')
        except (ValueError, TypeError):
            messages.error(request, 'Quantidade deve ser um número inteiro.')
    return redirect('bar_app:manage_stock')

@login_required
@user_passes_test(is_staff_user)
@transaction.atomic
def add_stock_dashboard(request):
    """Adicionar stock a um produto do painel (dashboard)"""
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            product = Product.objects.select_for_update().get(pk=form.cleaned_data['product'].pk)
            quantity = form.cleaned_data['quantity']
            movement = StockMovement(
                product=product, movement_type='in', quantity=quantity,
                reason='Adição via Dashboard', created_by=request.user
            )
            movement.save()
            cost_per_unit = product.purchase_price if product.purchase_price is not None else (product.price * Decimal('0.50'))
            total_cost = (cost_per_unit * Decimal(quantity)).quantize(Decimal('0.01'))
            messages.success(request, f'Stock de {product.name} aumentado em {quantity} unidades. Custo: €{total_cost}')
            return redirect('bar_app:finance_summary')
    else:
        form = AddStockForm()
    all_products = Product.objects.select_related('category').filter(is_available=True)
    categories = Category.objects.filter(is_active=True)
    return render(request, 'bar_app/dashboard/add_stock_dashboard.html', {
        'form': form, 'title': 'Adicionar Stock', 'all_products': all_products, 'categories': categories
    })

@login_required
@user_passes_test(is_staff_user)
def finance_summary(request):
    """Resumo financeiro"""
    tx_filter = request.GET.get('tx_type', 'all')
    
    transactions = Transaction.objects.select_related('user', 'order').all().order_by('-created_at')
    school_txs_qs = SchoolTransaction.objects.select_related('created_by').all().order_by('-created_at')
    total_topups = transactions.filter(transaction_type='topup').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_payments = transactions.filter(transaction_type='payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_refunds = transactions.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Calcular as despesas da escola (compra de stock, etc.)
    school_expenses = SchoolTransaction.objects.filter(movement_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_earned = total_payments - total_refunds - school_expenses

    today_dt = timezone.localtime().date()
    current_month_txs = transactions.filter(created_at__year=today_dt.year, created_at__month=today_dt.month)
    current_month_school_txs = SchoolTransaction.objects.filter(created_at__year=today_dt.year, created_at__month=today_dt.month)
    
    month_topups = current_month_txs.filter(transaction_type='topup').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_payments = current_month_txs.filter(transaction_type='payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_refunds = current_month_txs.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_school_expenses = current_month_school_txs.filter(movement_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    
    total_user_balance = User.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    def fmt_dec(v):
        v = Decimal(v or 0)
        q = v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return format(q, '0.2f').replace('.', ',')

    transactions_list = []
    
    # Adicionar transações de utilizadores se o filtro permitir
    if tx_filter in ['all', 'topup', 'payment', 'refund']:
        tx_qs = transactions
        if tx_filter != 'all':
            tx_qs = tx_qs.filter(transaction_type=tx_filter)
            
        for tx in tx_qs[:200]:
            transactions_list.append({
                'tx': tx, 'amount_str': fmt_dec(tx.amount), 'created_at': tx.created_at,
                'user_display': tx.user.get_full_name() or tx.user.username, 'tx_type': 'transaction'
            })
    
    # Adicionar transações da escola se o filtro permitir
    if tx_filter in ['all', 'expense', 'income']:
        stx_qs = school_txs_qs
        if tx_filter != 'all':
            stx_qs = stx_qs.filter(movement_type=tx_filter)
            
        for stx in stx_qs[:100]:
            transactions_list.append({
                'tx': stx, 'amount_str': fmt_dec(stx.amount), 'created_at': stx.created_at,
                'user_display': stx.created_by.get_full_name() or stx.created_by.username if stx.created_by else 'Sistema',
                'tx_type': 'school_transaction'
            })
    
    transactions_list.sort(key=lambda x: x['created_at'], reverse=True)
    transactions_list = transactions_list[:200]

    try:
        sa = SchoolAccount.objects.get(pk=1)
        school_balance_raw = sa.balance
    except Exception:
        school_balance_raw = Decimal('0.00')

    context = {
        'total_deposits': fmt_dec(total_topups),
        'total_sales': fmt_dec(total_payments),
        'total_refunds': fmt_dec(total_refunds),
        'total_expenses': fmt_dec(school_expenses),
        'net_earned': fmt_dec(net_earned),
        'month_deposits': fmt_dec(month_topups),
        'month_sales': fmt_dec(month_payments),
        'month_refunds': fmt_dec(month_refunds),
        'month_expenses': fmt_dec(month_school_expenses),
        'month_net': fmt_dec(month_payments - month_refunds - month_school_expenses),
        'current_month': today_dt.strftime('%B %Y'),
        'total_user_balance': fmt_dec(total_user_balance),
        'school_balance': fmt_dec(school_balance_raw),
        'transactions': transactions_list,
        'current_filter': tx_filter,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'bar_app/dashboard/partials/_finance_table.html', context)
        
    return render(request, 'bar_app/dashboard/finance_summary.html', context)

@login_required
@user_passes_test(is_staff_user)
def export_transactions_pdf(request):
    """Exportar histórico de transações para PDF"""
    tx_filter = request.GET.get('tx_type', 'all')
    
    # Reutilizar lógica de filtragem do finance_summary para consistência
    transactions_list = []
    
    def fmt_dec(v):
        from decimal import Decimal, ROUND_HALF_UP
        v = Decimal(v or 0)
        q = v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return format(q, '0.2f').replace('.', ',')

    if tx_filter in ['all', 'topup', 'payment', 'refund']:
        tx_qs = Transaction.objects.select_related('user').all().order_by('-created_at')
        if tx_filter != 'all':
            tx_qs = tx_qs.filter(transaction_type=tx_filter)
        for tx in tx_qs:
            transactions_list.append({
                'date': tx.created_at.strftime('%d/%m/%Y %H:%M'),
                'user': tx.user.get_full_name() or tx.user.username,
                'type': tx.get_transaction_type_display(),
                'amount': f"{fmt_dec(tx.amount)} €",
                'desc': tx.description,
                'created_at': tx.created_at,
                'raw_type': tx.transaction_type
            })

    if tx_filter in ['all', 'expense', 'income']:
        stx_qs = SchoolTransaction.objects.select_related('created_by').all().order_by('-created_at')
        if tx_filter != 'all':
            stx_qs = stx_qs.filter(movement_type=tx_filter)
        for stx in stx_qs:
            transactions_list.append({
                'date': stx.created_at.strftime('%d/%m/%Y %H:%M'),
                'user': stx.created_by.get_full_name() or stx.created_by.username if stx.created_by else 'Sistema',
                'type': stx.get_movement_type_display(),
                'amount': f"{fmt_dec(stx.amount)} €",
                'desc': stx.description,
                'created_at': stx.created_at,
                'raw_type': stx.movement_type
            })

    transactions_list.sort(key=lambda x: x['created_at'], reverse=True)

    # Preparar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    from bar_app.utils import _add_pdf_header
    _add_pdf_header(elements, "Relatório de Transações - Bar Escolar")
    
    styles = getSampleStyleSheet()
    filter_label = {
        'all': 'Todas as Transações',
        'topup': 'Carregamentos',
        'payment': 'Pagamentos',
        'refund': 'Reembolsos',
        'expense': 'Compras de Stock',
        'income': 'Receitas da Escola'
    }.get(tx_filter, tx_filter)
    
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=11, leading=14)
    elements.append(Paragraph(f"<b>Filtro aplicado:</b> {filter_label}", meta_style))
    elements.append(Paragraph(f"<b>Data de Emissão:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}", meta_style))
    elements.append(Spacer(1, 1*cm))

    # Tabela
    data = [['Data', 'Utilizador', 'Tipo', 'Montante', 'Descrição']]
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B4423')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (4, 1), (4, -1), 'LEFT'),
    ]

    for i, item in enumerate(transactions_list):
        data.append([item['date'], item['user'], item['type'], item['amount'], item['desc'][:50]])
        
        # Tipo Column Color (Index 2)
        rtype = item.get('raw_type', '')
        type_color = colors.black
        if rtype in ['topup']:
            type_color = colors.HexColor('#0d6efd') # Azul
        elif rtype in ['payment', 'income']:
            type_color = colors.HexColor('#198754') # Verde
        elif rtype in ['expense']:
            type_color = colors.HexColor('#dc3545') # Vermelho
        elif rtype in ['refund']:
            type_color = colors.HexColor('#fd7e14') # Laranja
        
        style_commands.append(('TEXTCOLOR', (2, i+1), (2, i+1), type_color))
        style_commands.append(('FONTNAME', (2, i+1), (2, i+1), 'Helvetica-Bold'))
        
        # Montante Column Bold (Index 3)
        style_commands.append(('FONTNAME', (3, i+1), (3, i+1), 'Helvetica-Bold'))

    table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 3*cm, 9*cm])
    table.setStyle(TableStyle(style_commands))
    elements.append(table)

    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transacoes_bar_escolar.pdf"'
    response.write(pdf)
    return response

@login_required
@user_passes_test(is_staff_user)
def all_reviews(request):
    """Ver todas as avaliações"""
    reviews = OrderReview.objects.all().order_by('-created_at')
    return render(request, 'bar_app/dashboard/all_reviews.html', {'reviews': reviews})

@login_required
@user_passes_test(is_staff_user)
def export_transactions_csv(request):
    """Exportar histórico de transações para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transacoes_bar_escolar.csv"'
    
    transactions = Transaction.objects.select_related('user').all().order_by('-created_at')
    
    # Gerar conteúdo CSV em memória com encoding windows-1252 para compatibilidade Excel
    output = []
    writer = csv.writer(type('Stream', (), {'write': lambda self, s: output.append(s)})(), delimiter=';')
    writer.writerow(['Data', 'Utilizador', 'Tipo', 'Valor', 'Descrição'])
    
    for tx in transactions:
        writer.writerow([
            tx.created_at.strftime('%d/%m/%Y %H:%M'),
            tx.user.username,
            tx.get_transaction_type_display(),
            f"{str(tx.amount).replace('.', ',')} €",
            tx.description
        ])
    
    # Combinar e codificar
    content = "".join(output).encode('windows-1252', errors='replace')
    response.write(content)
    return response

@login_required
@user_passes_test(is_staff_user)
def scan_qr(request):
    """Página de scan de QR Code para identificação de utilizadores"""
    return render(request, 'bar_app/dashboard/scan_qr.html')

@login_required
@user_passes_test(is_staff_user)
def quick_user_lookup(request):
    """Procura utilizador pelo ID do QR Code (username)"""
    username = request.GET.get('username')
    try:
        user = User.objects.get(username=username)
        data = {
            'success': True,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'user_type': user.get_user_type_display(),
            'balance': str(user.balance),
            'profile_url': reverse('bar_app:profile') + f'?user={user.username}', # Simulação de busca
            'recent_orders_url': reverse('bar_app:manage_orders') + f'?user={user.username}'
        }
    except User.DoesNotExist:
        data = {'success': False, 'error': 'Utilizador não encontrado'}
    
    return JsonResponse(data)

@login_required
@user_passes_test(is_staff_user)
def export_orders_csv(request):
    """Exportar lista de pedidos para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pedidos_bar_escolar.csv"'
    
    orders = Order.objects.select_related('user').prefetch_related('items__product').all().order_by('-created_at')
    
    # Gerar conteúdo CSV em memória com encoding windows-1252 para compatibilidade Excel
    output = []
    writer = csv.writer(type('Stream', (), {'write': lambda self, s: output.append(s)})(), delimiter=';')
    writer.writerow(['ID Pedido', 'Data Agendada', 'Data Criação', 'Utilizador', 'Estado', 'Total', 'Produtos'])
    
    for order in orders:
        items_str = ", ".join([f"{item.quantity}x {item.product.name}" for item in order.items.all()])
        
        writer.writerow([
            order.order_number,
            f"{order.scheduled_date.strftime('%d/%m/%Y')} {order.scheduled_time.strftime('%H:%M')}",
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            order.user.username,
            order.get_status_display(),
            f"{str(order.total_amount).replace('.', ',')} €",
            items_str
        ])
        
    # Combinar e codificar
    content = "".join(output).encode('windows-1252', errors='replace')
    response.write(content)
    return response

@login_required
@user_passes_test(is_staff_user)
def export_orders_pdf(request):
    """Exportar lista de pedidos para PDF"""
    orders = Order.objects.select_related('user').prefetch_related('items__product').all().order_by('-created_at')

    # Preparar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    from bar_app.utils import _add_pdf_header
    _add_pdf_header(elements, "Relatório de Pedidos - Bar Escolar")

    styles = getSampleStyleSheet()
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=11, leading=14)
    elements.append(Paragraph(f"<b>Data de Emissão:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}", meta_style))
    elements.append(Spacer(1, 1*cm))

    # Tabela de dados
    # Cabeçalho: ID, Data Agendada, Data Criação, Utilizador, Estado, Total
    data = [['ID', 'Agendado', 'Criado em', 'Utilizador', 'Estado', 'Total']]
    
    for order in orders:
        data.append([
            order.order_number,
            f"{order.scheduled_date.strftime('%d/%m/%Y')} {order.scheduled_time.strftime('%H:%M')}",
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            order.user.username,
            order.get_status_display(),
            f"€ {str(order.total_amount).replace('.', ',')}"
        ])

    table = Table(data, colWidths=[4.5*cm, 4*cm, 4.2*cm, 5.2*cm, 3.8*cm, 3*cm])
    # Estilos de tabela
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B4423')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    
    elements.append(Spacer(1, 2*cm))
    footer_style = ParagraphStyle('Footer', parent=styles['Italic'], alignment=1, textColor=colors.gray, fontSize=9)
    elements.append(Paragraph("Relatório gerado automaticamente pelo Sistema de Gestão do Bar Escolar", footer_style))

    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="pedidos_bar_escolar.pdf"'
    response.write(pdf)
    return response
