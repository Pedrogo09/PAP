"""
URLs da aplicação bar
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

app_name = 'bar_app'

urlpatterns = [
    # Service worker (PWA)
    path('service-worker.js', TemplateView.as_view(template_name='service-worker.js', content_type='application/javascript'), name='service_worker'),
    # Página inicial
    path('', views.home, name='home'),
    
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # Menu e produtos
    path('products/', views.menu, name='menu'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # Carrinho e pedidos
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Pedidos
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/status/', views.check_order_status, name='check_order_status'),
    path('order/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Perfil e saldo
    path('profile/', views.profile, name='profile'),
    path('topup/', views.topup, name='topup'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    
    # Painel administrativo (staff)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/add-stock/', views.add_stock_dashboard, name='add_stock_dashboard'),
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('dashboard/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('dashboard/stock/', views.manage_stock, name='manage_stock'),
    path('dashboard/stock/<int:product_id>/replenish/', views.replenish_stock, name='replenish_stock'),
    path('dashboard/finance/', views.finance_summary, name='finance_summary'),
    path('dashboard/finance/export/', views.export_transactions_csv, name='export_transactions_csv'),
    path('dashboard/finance/export-pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),
    path('dashboard/orders/export/', views.export_orders_csv, name='export_orders_csv'),
    path('dashboard/orders/export-pdf/', views.export_orders_pdf, name='export_orders_pdf'),
    # Avaliações
    path('order/<int:order_pk>/review/', views.submit_review, name='submit_review'),
    path('dashboard/reviews/', views.all_reviews, name='all_reviews'),
    # QR Code Scanning
    path('dashboard/scan/', views.scan_qr, name='scan_qr'),
    path('dashboard/user-lookup/', views.quick_user_lookup, name='quick_user_lookup'),
    # AI Assistant
    path('ai-chat/', views.ai_chat_response, name='ai_chat_response'),
]
