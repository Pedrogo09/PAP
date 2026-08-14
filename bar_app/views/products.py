from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from ..models import Product, Category, FavoriteProduct, OrderItem

def home(request):
    """Página inicial"""
    featured_products = Product.objects.filter(is_available=True)[:6]
    categories = Category.objects.filter(is_active=True)
    
    for p in featured_products:
        p.current_price = p.get_price_for_user(request.user)
        
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'bar_app/home.html', context)

def menu(request):
    """Listagem de produtos (menu) com suporte a AJAX"""
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    price_filter = request.GET.get('price')
    sort_by = request.GET.get('sort')
    show_favorites = request.GET.get('favorites') == 'true'
    
    products = Product.objects.filter(is_available=True)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
        
    if price_filter:
        if price_filter == 'under_1':
            products = products.filter(price__lte=1)
        elif price_filter == 'under_2':
            products = products.filter(price__lte=2)
        elif price_filter == 'over_2':
            products = products.filter(price__gt=2)
            
    if sort_by:
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'name_asc':
            products = products.order_by('name')
        elif sort_by == 'name_desc':
            products = products.order_by('-name')
    
    if show_favorites and request.user.is_authenticated:
        favorite_ids = FavoriteProduct.objects.filter(user=request.user).values_list('product_id', flat=True)
        products = products.filter(id__in=favorite_ids)
        
    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = list(FavoriteProduct.objects.filter(user=request.user).values_list('product_id', flat=True))

    # Prefetch related data to avoid N+1 queries
    products = products.select_related('category')
    
    for p in products:
        p.current_price = p.get_price_for_user(request.user)
        p.allergen_conflicts = p.get_user_allergens_conflict(request.user)

    # Calculate suggested products (most sold per category) - Otimizado para evitar N+1 queries
    suggested_products = []
    all_categories = Category.objects.filter(is_active=True).prefetch_related(
        'products__orderitem_set'
    )
    for cat in all_categories:
        most_sold = Product.objects.filter(
            category=cat, 
            is_available=True
        ).annotate(
            total_sold=Coalesce(Sum('orderitem__quantity'), 0)
        ).order_by('-total_sold', 'name').first()
        if most_sold:
            most_sold.current_price = most_sold.get_price_for_user(request.user)
            most_sold.allergen_conflicts = most_sold.get_user_allergens_conflict(request.user)
            suggested_products.append(most_sold)

    # Context items for the full page
    categories = Category.objects.all()
    categories_data = [{
        'id': cat.id,
        'name': cat.name,
        'image_url': cat.image.url if cat.image else None,
        'is_selected': str(cat.id) == category_id
    } for cat in categories]

    price_options = [
        {'value': 'under_1', 'label': 'Até 1€', 'is_selected': price_filter == 'under_1'},
        {'value': 'under_2', 'label': 'Até 2€', 'is_selected': price_filter == 'under_2'},
        {'value': 'over_2', 'label': 'Mais de 2€', 'is_selected': price_filter == 'over_2'},
    ]
    
    sort_options = [
        {'value': 'price_asc', 'label': 'Mais barato', 'is_selected': sort_by == 'price_asc'},
        {'value': 'price_desc', 'label': 'Mais caro', 'is_selected': sort_by == 'price_desc'},
        {'value': 'name_asc', 'label': 'Nome: A-Z', 'is_selected': sort_by == 'name_asc'},
    ]

    context = {
        'products': products,
        'categories_data': categories_data,
        'price_options': price_options,
        'sort_options': sort_options,
        'search': search,
        'show_favorites': show_favorites,
        'user_favorites': user_favorites,
        'category_id': category_id,
        'suggested_products': suggested_products,
    }

    # AJAX Response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'bar_app/menu_products_partial.html', context)
        
    return render(request, 'bar_app/menu.html', context)

def product_detail(request, pk):
    """Detalhe de um produto"""
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(pk=pk)[:4]
    
    product.current_price = product.get_price_for_user(request.user)
    product.allergen_conflicts = product.get_user_allergens_conflict(request.user)
    for p in related_products:
        p.current_price = p.get_price_for_user(request.user)
        p.allergen_conflicts = p.get_user_allergens_conflict(request.user)
        
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'bar_app/product_detail.html', context)

@login_required
def cart(request):
    """Carrinho de compras"""
    cart_items = request.session.get('cart', {})
    items = []
    total = 0
    
    for product_id, quantity in cart_items.items():
        try:
            product = Product.objects.get(pk=product_id)
            current_price = product.get_price_for_user(request.user)
            subtotal = current_price * quantity
            total += subtotal
            items.append({
                'product': product,
                'current_price': current_price,
                'quantity': quantity,
                'subtotal': subtotal,
                'allergen_conflicts': product.get_user_allergens_conflict(request.user),
            })
        except Product.DoesNotExist:
            continue
    
    context = {
        'items': items,
        'total': total,
    }
    return render(request, 'bar_app/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    """Adicionar produto ao carrinho"""
    product = get_object_or_404(Product, pk=product_id)
    
    if not product.is_in_stock():
        messages.error(request, 'Produto sem stock.')
        return redirect('bar_app:menu')
    
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1
    
    request.session['cart'] = cart
    
    # Calculate cart total
    total_price = 0
    total_items = sum(cart.values())
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(pk=pid)
            total_price += p.get_price_for_user(request.user) * qty
        except Product.DoesNotExist:
            pass

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'product_name': product.name,
            'total_items': total_items,
            'total_price': f"{total_price:.2f}",
            'cart_count': len(cart)
        })
            
    msg_html = f'''
    <div class="d-flex justify-content-between align-items-center" style="min-width: 250px;">
        <div>
            <strong>{product.name}</strong> adicionado.<br>
            <small class="text-muted">{total_items} item(s) • Total: €{total_price:.2f}</small>
        </div>
        <a href="/cart/" class="btn btn-sm btn-primary ms-3">Ver Carrinho</a>
    </div>
    '''
    
    messages.success(request, msg_html, extra_tags='cart-toast')
    return redirect('bar_app:menu')

@login_required
def remove_from_cart(request, product_id):
    """Remover produto do carrinho"""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, 'Produto removido do carrinho.')
    
    return redirect('bar_app:cart')

@login_required
def update_cart(request, product_id):
    """Atualizar quantidade no carrinho"""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            
            if quantity > 0:
                cart[product_id_str] = quantity
            else:
                cart.pop(product_id_str, None)
            
            request.session['cart'] = cart
        except (ValueError, TypeError):
            pass
    
    return redirect('bar_app:cart')

@login_required
def toggle_favorite(request, product_id):
    """Adiciona ou remove um produto dos favoritos via AJAX"""
    product = get_object_or_404(Product, id=product_id)
    favorite, created = FavoriteProduct.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
        
    return JsonResponse({
        'success': True,
        'is_favorite': is_favorite,
        'product_id': product_id
    })
