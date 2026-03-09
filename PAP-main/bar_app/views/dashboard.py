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
    today = timezone.now().date()
    total_orders_today = Order.objects.filter(scheduled_date=today).count()
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    low_stock_products = Product.objects.filter(stock__lte=F('min_stock')).count()
    critical_stock = Product.objects.filter(stock__lte=F('min_stock')).order_by('stock')[:5]
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    top_products = Product.objects.annotate(total_sold=Sum('orderitem__quantity')).order_by('-total_sold')[:5]
    
    period = request.GET.get('period', '7days')
    last_7_days = []
    sales_by_day = []
    
    if period == 'best':
        best_month_data = Order.objects.filter(status__in=['ready', 'delivered', 'completed']).annotate(
            month=TruncMonth('scheduled_date')
        ).values('month').annotate(total=Count('id')).order_by('-total').first()
        if best_month_data and best_month_data['month']:
            bm = best_month_data['month']
            _, num_days = calendar.monthrange(bm.year, bm.month)
            for d in range(1, num_days + 1):
                day_date = bm.replace(day=d)
                count = Order.objects.filter(scheduled_date=day_date, status__in=['ready', 'delivered', 'completed']).count()
                last_7_days.append(f"{d}/{bm.month:02d}")
                sales_by_day.append(count)
        else:
            last_7_days, sales_by_day = [today.strftime('%d/%m')], [0]
    elif period == '30days':
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            count = Order.objects.filter(scheduled_date=day, status__in=['ready', 'delivered', 'completed']).count()
            last_7_days.append(day.strftime('%d/%m'))
            sales_by_day.append(count)
    else:
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_name = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom'][day.weekday()]
            count = Order.objects.filter(scheduled_date=day, status__in=['ready', 'delivered', 'completed']).count()
            last_7_days.append(f"{day_name} {day.strftime('%d/%m')}")
            sales_by_day.append(count)
    
    top_product_names = [p.name[:15] for p in top_products]
    top_product_quantities = [p.total_sold or 0 for p in top_products]
    school_account = SchoolAccount.objects.get(pk=1)
    
    context = {
        'total_orders_today': total_orders_today, 'pending_orders': pending_orders,
        'low_stock_products': low_stock_products, 'critical_stock': critical_stock,
        'recent_orders': recent_orders, 'top_products': top_products,
        'last_7_days': last_7_days, 'sales_by_day': sales_by_day,
        'top_product_names': top_product_names, 'top_product_quantities': top_product_quantities,
        'school_balance': f"{school_account.balance}".replace('.', ','),
        'selected_period': period,
    }
    return render(request, 'bar_app/dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def manage_products(request):
    """Gestão de produtos"""
    products = Product.objects.all()
    return render(request, 'bar_app/dashboard/products.html', {'products': products})

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
def replenish_stock(request, product_id):
    """Repor stock de um produto"""
    product = get_object_or_404(Product, pk=product_id)
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
def add_stock_dashboard(request):
    """Adicionar stock a um produto do painel (dashboard)"""
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            movement = StockMovement(
                product=product, movement_type='in', quantity=quantity,
                reason='Adição via Dashboard', created_by=request.user
            )
            movement.save()
            cost_per_unit = product.price * Decimal('0.50')
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
    transactions = Transaction.objects.select_related('user', 'order').all().order_by('-created_at')
    total_topups = transactions.filter(transaction_type='topup').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_payments = transactions.filter(transaction_type='payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_refunds = transactions.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_earned = total_payments - total_refunds

    today_dt = date.today()
    current_month_txs = transactions.filter(created_at__year=today_dt.year, created_at__month=today_dt.month)
    month_topups = current_month_txs.filter(transaction_type='topup').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_payments = current_month_txs.filter(transaction_type='payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_refunds = current_month_txs.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_user_balance = User.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    def fmt_dec(v):
        v = Decimal(v or 0)
        q = v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return format(q, '0.2f').replace('.', ',')

    transactions_list = []
    for tx in transactions[:200]:
        transactions_list.append({
            'tx': tx, 'amount_str': fmt_dec(tx.amount), 'created_at': tx.created_at,
            'user_display': tx.user.get_full_name() or tx.user.username, 'tx_type': 'transaction'
        })
    
    school_txs = SchoolTransaction.objects.select_related('created_by').all().order_by('-created_at')[:100]
    for stx in school_txs:
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
        'total_topups': fmt_dec(total_topups), 'total_payments': fmt_dec(total_payments),
        'total_refunds': fmt_dec(total_refunds), 'net_earned': fmt_dec(net_earned),
        'month_topups': fmt_dec(month_topups), 'month_payments': fmt_dec(month_payments),
        'month_refunds': fmt_dec(month_refunds), 'month_net': fmt_dec(month_payments - month_refunds),
        'current_month': today_dt.strftime('%B %Y'), 'total_user_balance': fmt_dec(total_user_balance),
        'school_balance': fmt_dec(school_balance_raw), 'transactions': transactions_list,
    }
    return render(request, 'bar_app/dashboard/finance_summary.html', context)

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
    
    # Adicionar BOM para Excel em português reconhecer caracteres especiais
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Data', 'Utilizador', 'Tipo', 'Valor', 'Descrição'])
    
    transactions = Transaction.objects.select_related('user').all().order_by('-created_at')
    for tx in transactions:
        writer.writerow([
            tx.created_at.strftime('%d/%m/%Y %H:%i'),
            tx.user.username,
            tx.get_transaction_type_display(),
            str(tx.amount).replace('.', ','),
            tx.description
        ])
    
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
