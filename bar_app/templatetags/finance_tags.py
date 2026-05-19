from django import template
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from django.utils import timezone
from datetime import date
from bar_app.models import User, Transaction, SchoolAccount, SchoolTransaction

register = template.Library()

@register.simple_tag
def get_finance_data():
    def fmt_dec(v):
        v = Decimal(v or 0)
        q = v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return format(q, '0.2f').replace('.', ',')

    transactions = Transaction.objects.all()
    total_topups = transactions.filter(transaction_type='topup').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_payments = transactions.filter(transaction_type='payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_refunds = transactions.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    school_expenses = SchoolTransaction.objects.filter(movement_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # No novo modelo, total_payments já é a receita bruta das vendas
    # total_refunds são os estornos
    # school_expenses são os custos de stock
    net_earned = total_payments - total_refunds - school_expenses

    today_dt = date.today()
    current_month_txs = transactions.filter(created_at__year=today_dt.year, created_at__month=today_dt.month)
    current_month_school_txs = SchoolTransaction.objects.filter(created_at__year=today_dt.year, created_at__month=today_dt.month)
    
    month_topups = current_month_txs.filter(transaction_type='topup').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_payments = current_month_txs.filter(transaction_type='payment').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_refunds = current_month_txs.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_school_expenses = current_month_school_txs.filter(movement_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_user_balance = User.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    try:
        sa = SchoolAccount.objects.get(pk=1)
        school_balance_raw = sa.balance
    except SchoolAccount.DoesNotExist:
        school_balance_raw = Decimal('0.00')

    return {
        'total_deposits': fmt_dec(total_topups),  # Saldo total depositado (não é lucro)
        'total_sales': fmt_dec(total_payments),    # Receita bruta de vendas
        'total_refunds': fmt_dec(total_refunds),
        'total_expenses': fmt_dec(school_expenses),
        'net_earned': fmt_dec(net_earned),         # Lucro real
        'month_deposits': fmt_dec(month_topups),
        'month_sales': fmt_dec(month_payments),
        'month_refunds': fmt_dec(month_refunds),
        'month_expenses': fmt_dec(month_school_expenses),
        'month_net': fmt_dec(month_payments - month_refunds - month_school_expenses),
        'current_month': today_dt.strftime('%B %Y'),
        'total_user_balance': fmt_dec(total_user_balance),
        'school_balance': fmt_dec(school_balance_raw),
    }

@register.inclusion_tag('bar_app/dashboard/partials/_finance_cards.html')
def render_finance_cards():
    return get_finance_data()
