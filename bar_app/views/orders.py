import os
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse
from ..models import (
    Order, OrderItem, Transaction, StockMovement, 
    Product, WeekdayAvailability, SchoolAccount, SchoolTransaction
)
from ..forms import OrderForm, TopUpForm, OrderReviewForm
from ..utils import generate_topup_pdf, generate_order_pdf
from .auth import is_staff_user

@login_required
def checkout(request):
    """Finalizar pedido"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'O seu carrinho está vazio.')
        return redirect('bar_app:menu')
    
    if request.method == 'POST':
        post_data = request.POST.copy()
        hour = request.POST.get('scheduled_hour')
        minute = request.POST.get('scheduled_minute')
        if hour and minute and not request.POST.get('scheduled_time'):
            post_data['scheduled_time'] = f"{hour}:{minute}"

        form = OrderForm(post_data)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            
            total = 0
            for product_id, quantity in cart.items():
                try:
                    product = Product.objects.get(pk=product_id)
                    if product.stock < quantity:
                        messages.error(request, f'Stock insuficiente para {product.name}.')
                        order.delete()
                        return redirect('bar_app:cart')
                    
                    unit_price = product.get_price_for_user(request.user)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price
                    )
                    
                    StockMovement.objects.create(
                        product=product,
                        movement_type='out',
                        quantity=quantity,
                        reason=f'Pedido {order.order_number}',
                        order=order,
                        created_by=request.user
                    )
                    total += unit_price * quantity
                except Product.DoesNotExist:
                    continue
            
            order.calculate_total()
            
            if order.payment_method == 'card':
                if request.user.balance < order.total_amount:
                    messages.error(request, 'Saldo insuficiente.')
                    order.delete()
                    return redirect('bar_app:topup')

                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='payment',
                    amount=order.total_amount,
                    order=order,
                    description=f'Pagamento pedido {order.order_number}'
                )

                # Adicionar pontos de fidelidade (1 ponto por €)
                request.user.loyalty_points += int(order.total_amount)
                request.user.save()

                # Atualizar Saldo da Escola (Venda Efetuada)
                try:
                    sa, _ = SchoolAccount.objects.get_or_create(pk=1, defaults={'balance': Decimal('0.00')})
                    sa.balance += order.total_amount
                    sa.save()
                    SchoolTransaction.objects.create(
                        school_account=sa, movement_type='income', amount=order.total_amount,
                        description=f'Venda (Pedido {order.order_number}) - Utilizador: {request.user.username}',
                        created_by=request.user
                    )
                except Exception:
                    pass

                pdf_buffer = generate_order_pdf(order, transaction)
                filename = f"order_{order.pk}.pdf"
                receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
                os.makedirs(receipts_dir, exist_ok=True)
                file_path = os.path.join(receipts_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(pdf_buffer.getvalue())

                from ..utils import send_pdf_email
                send_pdf_email(request.user, 'Recibo de Pedido - Bar Escolar', 'Segue em anexo o seu recibo.', pdf_buffer, filename)

                request.session['cart'] = {}
                download_url = os.path.join(settings.MEDIA_URL, 'receipts', filename)
                msg = mark_safe(f'Pedido confirmado. <a href="{download_url}">Descarregar recibo (PDF)</a>')
                messages.success(request, msg)
                return redirect('bar_app:order_detail', pk=order.pk)
            
            # Tratamento para pagamentos via ATM/Multibanco ou outros (Dinheiro)
            if order.payment_method == 'atm':
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='payment',
                    amount=order.total_amount,
                    order=order,
                    description=f'Pagamento via Multibanco - Pedido {order.order_number}'
                )
                try:
                    sa, _ = SchoolAccount.objects.get_or_create(pk=1, defaults={'balance': Decimal('0.00')})
                    sa.balance += order.total_amount
                    sa.save()
                    SchoolTransaction.objects.create(
                        school_account=sa, movement_type='income', amount=order.total_amount,
                        description=f'Venda ATM (Pedido {order.order_number})',
                        created_by=request.user
                    )
                except Exception:
                    pass

            request.session['cart'] = {}
            messages.success(request, f'Pedido {order.order_number} criado com sucesso!')
            return redirect('bar_app:order_detail', pk=order.pk)
    else:
        form = OrderForm()
    
    items = []
    total = 0
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            current_price = product.get_price_for_user(request.user)
            subtotal = current_price * quantity
            total += subtotal
            items.append({
                'product': product, 
                'current_price': current_price,
                'quantity': quantity, 
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            continue
    
    schedules = []
    for wd in range(7):
        qs = WeekdayAvailability.objects.filter(weekday=wd, is_active=True)
        if qs.exists():
            start = min(q.start_time for q in qs)
            end = max(q.end_time for q in qs)
            schedules.append({'is_open': True, 'opening_time': start.strftime('%H:%M'), 'closing_time': end.strftime('%H:%M')})
        else:
            schedules.append({'is_open': False, 'opening_time': '00:00', 'closing_time': '00:00'})

    context = {
        'form': form, 'items': items, 'total': total,
        'schedule_json': json.dumps(schedules),
        'today': timezone.localtime().date().isoformat(),
        'default_date': timezone.localtime().date().isoformat(),
    }
    return render(request, 'bar_app/checkout.html', context)

@login_required
def order_list(request):
    """Listar pedidos do utilizador"""
    orders = Order.objects.filter(user=request.user)
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    sort_filter = request.GET.get('sort', '-created_at')
    if sort_filter in ['created_at', '-created_at', 'total_amount', '-total_amount']:
        orders = orders.order_by(sort_filter)
    else:
        orders = orders.order_by('-created_at')
        
    from django.db.models import Sum
    total_spent = orders.exclude(status='cancelled').aggregate(total=Sum('total_amount'))['total'] or 0
    delivered_count = orders.filter(status='delivered').count()
    pending_count = orders.filter(status='pending').count()
    
    context = {
        'orders': orders,
        'total_spent': f"{total_spent:.2f}".replace('.', ','),
        'delivered_count': delivered_count,
        'pending_count': pending_count
    }
    
    return render(request, 'bar_app/order_list.html', context)

@login_required
def order_detail(request, pk):
    """Detalhe de um pedido"""
    order = get_object_or_404(Order, pk=pk)
    if order.user != request.user and not is_staff_user(request.user):
        messages.error(request, 'Não tem permissão para ver este pedido.')
        return redirect('bar_app:order_list')
    return render(request, 'bar_app/order_detail.html', {'order': order})

@login_required
def cancel_order(request, pk):
    """Cancelar um pedido"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    can, needs_fine, fine_amount = order.get_cancellation_info()
    if can:
        order.status = 'cancelled'
        order.save()
        
        # Repor stock
        for item in order.items.all():
            StockMovement.objects.create(
                product=item.product, movement_type='in', quantity=item.quantity,
                reason=f'Cancelamento pedido {order.order_number}', created_by=request.user
            )
            
        if order.payment_method == 'card':
            refund_amount = order.total_amount - fine_amount
            
            # Reembolso principal
            Transaction.objects.create(
                user=request.user, transaction_type='refund', amount=refund_amount,
                order=order, description=f'Reembolso pedido {order.order_number}' + (f' (Multa 10% aplicada)' if needs_fine else '')
            )
            
            # Atualizar saldo do utilizador
            user = request.user
            user.balance += refund_amount
            user.save()
            
            # Reembolsar Saldo da Escola (Venda Cancelada)
            try:
                sa = SchoolAccount.objects.get(pk=1)
                sa.balance -= refund_amount
                sa.save()
                SchoolTransaction.objects.create(
                    school_account=sa, movement_type='expense', amount=refund_amount,
                    description=f'Estorno Venda (Cancelamento {order.order_number})',
                    created_by=request.user
                )
            except Exception:
                pass
        
        if needs_fine:
            messages.warning(request, f'Pedido cancelado. Foi aplicada uma multa de 10% (€{fine_amount}) por cancelamento tardio.')
        else:
            messages.success(request, 'Pedido cancelado com sucesso.')
    else:
        messages.error(request, 'Este pedido não pode ser cancelado (já passou do tempo limite ou está em preparação).')
    return redirect('bar_app:order_detail', pk=pk)

@login_required
def profile(request):
    """Perfil do utilizador com suporte a edição de dados e alérgenos"""
    from ..forms import UserProfileForm
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('bar_app:profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    recent_orders = Order.objects.filter(user=request.user)[:5]
    recent_transactions = Transaction.objects.filter(user=request.user)[:10]
    context = {
        'form': form,
        'recent_orders': recent_orders, 
        'recent_transactions': recent_transactions
    }
    return render(request, 'bar_app/profile.html', context)

@login_required
def topup(request):
    """Carregar saldo"""
    step = request.GET.get('step') or request.POST.get('step') or '1'
    if request.method == 'POST':
        if 'payment_method' not in request.POST and request.POST.get('step') != '3':
            amount_raw = request.POST.get('amount')
            if not amount_raw:
                messages.error(request, 'Valor inválido.')
                return render(request, 'bar_app/topup.html', {'step': '1', 'form': TopUpForm(request.POST)})
            amount_norm = str(amount_raw).strip().replace(',', '.')
            try:
                amount = Decimal(amount_norm)
            except Exception:
                messages.error(request, 'Valor inválido.')
                return render(request, 'bar_app/topup.html', {'step': '1', 'form': TopUpForm(request.POST), 'amount': amount_raw})
            if amount < Decimal('5') or amount > Decimal('100'):
                messages.error(request, 'Por favor introduza um valor entre €5 e €100')
                return render(request, 'bar_app/topup.html', {'step': '1', 'form': TopUpForm(request.POST), 'amount': amount})
            request.session['topup_amount'] = str(amount)
            return render(request, 'bar_app/topup.html', {'step': '2', 'amount': amount})

        if 'payment_method' in request.POST:
            payment_method = request.POST.get('payment_method')
            amount_str = request.POST.get('amount') or request.session.get('topup_amount')
            try:
                amount = Decimal(amount_str)
            except Exception:
                messages.error(request, 'Valor inválido. Por favor tente novamente.')
                return redirect('bar_app:topup')

            transaction = Transaction.objects.create(
                user=request.user, transaction_type='topup', amount=amount,
                description=f'Carregamento via {payment_method}'
            )

            # Registar entrada no saldo da escola para controlo de caixa/banco
            try:
                sa, _ = SchoolAccount.objects.get_or_create(pk=1, defaults={'balance': Decimal('0.00')})
                sa.balance += amount
                sa.save()
                SchoolTransaction.objects.create(
                    school_account=sa, movement_type='income', amount=amount,
                    description=f'Carregamento do utilizador {request.user.username}',
                    created_by=request.user
                )
            except Exception:
                pass

            request.session.pop('topup_amount', None)
            pdf_buffer = generate_topup_pdf(transaction)
            filename = f"topup_{transaction.pk}.pdf"
            receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
            os.makedirs(receipts_dir, exist_ok=True)
            file_path = os.path.join(receipts_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())

            from ..utils import send_pdf_email
            send_pdf_email(request.user, 'Comprovativo de Carregamento - Bar Escolar', 'Segue em anexo o seu comprovativo de carregamento.', pdf_buffer, filename)

            download_url = os.path.join(settings.MEDIA_URL, 'receipts', filename)
            msg = mark_safe(f'Saldo carregado com sucesso. <a href="{download_url}">Descarregar comprovativo (PDF)</a>')
            messages.success(request, msg)
            return redirect('bar_app:profile')

        if request.POST.get('step') == '3':
            messages.success(request, 'Pagamento processado com sucesso.')
            return redirect('bar_app:profile')

    form = TopUpForm()
    context = {'form': form, 'step': str(step)}
    if 'topup_amount' in request.session and step == '2':
        try:
            context['amount'] = Decimal(request.session.get('topup_amount'))
        except Exception:
            context['amount'] = None
    return render(request, 'bar_app/topup.html', context)

@login_required
def transaction_list(request):
    """Histórico de transações"""
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'bar_app/transaction_list.html', {'transactions': transactions})

@login_required
def submit_review(request, order_pk):
    """Submeter uma avaliação para um pedido"""
    order = get_object_or_404(Order, pk=order_pk, user=request.user)
    if order.status not in ['delivered', 'cancelled']:
        messages.error(request, 'Ainda não pode avaliar este pedido.')
        return redirect('bar_app:order_detail', pk=order_pk)
    if hasattr(order, 'review'):
        messages.warning(request, 'Este pedido já foi avaliado.')
        return redirect('bar_app:order_detail', pk=order_pk)
    
    if request.method == 'POST':
        form = OrderReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.save()
            messages.success(request, 'Obrigado pela sua avaliação!')
            return redirect('bar_app:order_detail', pk=order_pk)
    else:
        form = OrderReviewForm()
    return render(request, 'bar_app/submit_review.html', {'form': form, 'order': order})

@login_required
def check_order_status(request, pk):
    """Retorna o estado atual do pedido em JSON para polling AJAX"""
    order = get_object_or_404(Order, pk=pk)
    if order.user != request.user and not is_staff_user(request.user):
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    return JsonResponse({
        'status': order.status,
        'status_display': order.get_status_display(),
        'is_ready': order.status == 'ready',
        'is_delivered': order.status == 'delivered'
    })

@login_required
def check_all_ready_orders(request):
    """Retorna todos os pedidos do utilizador com estado 'ready' (Pronto)"""
    ready_orders = Order.objects.filter(user=request.user, status='ready')
    data = []
    for order in ready_orders:
        data.append({
            'id': order.id,
            'number': order.order_number,
            'scheduled_time': order.scheduled_time.strftime('%H:%M') if order.scheduled_time else '',
            'total': f"{order.total_amount:.2f}".replace('.', ',')
        })
    return JsonResponse({'ready_orders': data})
