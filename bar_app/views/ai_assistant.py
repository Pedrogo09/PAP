import json
import time
import requests
import re
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Sum, F, Count
from ..models import Product, Order, Transaction, Category, SchoolAccount
from django.contrib.auth import get_user_model
from decimal import Decimal

GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', '')


def detect_intent(user_message):
    """
    Detecta a intenção da pergunta para carregar apenas o contexto necessário.
    Retorna uma lista de contextos necessários.
    """
    message_lower = user_message.lower()
    
    intents = []
    
    # Palavras-chave em português e inglês
    menu_keywords = ['menu', 'produt', 'item', 'opção', 'tem', 'disponível', 'comer', 'beber', 
                    'menu', 'product', 'item', 'option', 'have', 'available', 'eat', 'drink']
    financial_keywords = ['fatur', 'lucr', 'receit', 'cust', 'dinheiro', 'saldo', 'venda', 'preço',
                         'revenue', 'profit', 'cost', 'money', 'balance', 'sale', 'price']
    stock_keywords = ['stock', 'quantidade', 'resta', 'inventário', 'armazém',
                     'stock', 'quantity', 'remaining', 'inventory', 'warehouse']
    user_keywords = ['aluno', 'professor', 'funcionário', 'utilizad', 'pessoa', 'cliente',
                    'student', 'teacher', 'staff', 'user', 'person', 'customer']
    cart_keywords = ['carrinho', 'adicion', 'meter', 'coloc', 'comprar', 'pedido',
                     'cart', 'add', 'put', 'buy', 'order']
    
    # Detectar intenções
    if any(kw in message_lower for kw in menu_keywords):
        intents.append('menu')
    
    if any(kw in message_lower for kw in financial_keywords):
        intents.append('financial')
    
    if any(kw in message_lower for kw in stock_keywords):
        intents.append('stock')
    
    if any(kw in message_lower for kw in user_keywords):
        intents.append('users')
    
    if any(kw in message_lower for kw in cart_keywords):
        intents.append('menu')  # Carrinho precisa do menu para IDs
    
    # Se não detectar intenção específica, usar contexto mínimo
    if not intents:
        intents.append('minimal')
    
    return intents


def get_minimal_context(user):
    """Contexto mínimo para perguntas gerais"""
    user_type_en = {
        'admin': 'Administrator',
        'staff': 'Staff / Bar Employee',
        'teacher': 'Teacher',
        'student': 'Student'
    }.get(user.user_type, 'User')
    
    return (
        f"Tu és o 'Barista AI', o assistente inteligente do Bar Escolar.\n"
        f"O utilizador atual é um {user.get_user_type_display()} ({user_type_en}).\n"
    )


def get_menu_context():
    """Contexto com apenas o menu de produtos"""
    products = Product.objects.filter(is_available=True).select_related('category')
    
    context = "MENU DISPONÍVEL / AVAILABLE MENU:\n"
    for p in products:
        context += f"- ID: {p.id} | {p.name}: €{p.price} ({p.category.name if p.category else 'Geral'})\n"
    
    return context


def get_financial_context():
    """Contexto com dados financeiros (apenas admin/staff)"""
    User = get_user_model()
    
    # Query otimizada para obter todos os dados em uma única operação
    all_products = Product.objects.filter(is_available=True)
    
    total_stock_cost = sum(
        p.stock * (p.purchase_price if p.purchase_price else (p.price * Decimal('0.50')))
        for p in all_products
    )
    potential_revenue = sum(p.stock * p.price for p in all_products)
    potential_profit = potential_revenue - total_stock_cost
    
    school_balance = SchoolAccount.objects.get(pk=1).balance
    total_user_balance = User.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    
    context = (
        f"Saldo da Escola: €{school_balance}\n"
        f"Saldo Agregado dos Utilizadores: €{total_user_balance:.2f}\n"
        f"Custo Total do Stock: €{total_stock_cost:.2f}\n"
        f"Receita Potencial: €{potential_revenue:.2f}\n"
        f"Lucro Potencial: €{potential_profit:.2f}\n"
    )
    
    return context


def get_stock_context():
    """Contexto com dados de stock"""
    products = Product.objects.filter(is_available=True).select_related('category')
    low_stock = Product.objects.filter(stock__lte=F('min_stock'))
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    
    context = f"Pedidos Pendentes: {pending_orders}\n"
    context += "PRODUTOS COM STOCK BAIXO:\n"
    for lp in low_stock:
        context += f"- {lp.name}: Restam {lp.stock} (Mínimo: {lp.min_stock})\n"
    
    context += "\nSTOCK DE TODOS OS PRODUTOS:\n"
    for p in products:
        context += f"- {p.name}: Stock={p.stock}\n"
    
    return context


def get_user_stats_context():
    """Contexto com estatísticas de utilizadores"""
    User = get_user_model()
    
    # Query otimizada - uma única query com agregação
    user_counts =	User.objects.values('user_type').annotate(count=Count('id'))
    counts_dict = {item['user_type']: item['count'] for item in user_counts}
    
    total_users = sum(counts_dict.values())
    students = counts_dict.get('student', 0)
    teachers = counts_dict.get('teacher', 0)
    staff = counts_dict.get('staff', 0)
    admins = counts_dict.get('admin', 0)
    
    context = (
        f"Total de Utilizadores: {total_users}\n"
        f"Alunos: {students}\n"
        f"Professores: {teachers}\n"
        f"Funcionários: {staff}\n"
        f"Admins: {admins}\n"
    )
    
    return context


def build_context(user, intents):
    """Constrói o contexto baseado nas intenções detectadas"""
    context = get_minimal_context(user)
    
    # Adicionar permissão note para não-admin/staff
    if user.user_type not in ['staff', 'admin']:
        context += "\nNota: Não tens acesso a dados administrativos.\n"
        return context
    
    # Adicionar contextos baseados nas intenções
    if 'menu' in intents:
        context += "\n" + get_menu_context()
    
    if 'financial' in intents:
        context += "\n--- DADOS FINANCEIROS ---\n" + get_financial_context()
    
    if 'stock' in intents:
        context += "\n--- DADOS DE STOCK ---\n" + get_stock_context()
    
    if 'users' in intents:
        context += "\n--- ESTATÍSTICAS DE UTILIZADORES ---\n" + get_user_stats_context()
    
    # Se for minimal mas admin/staff, adicionar nota
    if 'minimal' in intents:
        context += "\nNota: Tens acesso a dados administrativos se precisares.\n"
    
    return context


@login_required
def ai_chat_response(request):
    """View que processa a pergunta do utilizador e responde usando IA com contexto otimizado"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
    except:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)
    
    # 1. Detectar intenção da pergunta
    intents = detect_intent(user_message)
    
    # 2. Construir contexto seletivo
    context = build_context(request.user, intents)
    
    # 3. Verificar API Key
    if not GEMINI_API_KEY:
        return JsonResponse({
            'response': f"Olá! Sou o Barista AI. (Configuração: Adiciona a tua GEMINI_API_KEY no .env). Recebi: '{user_message}'",
            'debug_context': context
        })
    
    # 4. Endpoint Gemini (modelo correto)
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    
    # 5. Prompt simplificado
    prompt = (
        f"REGRAS:\n"
        f"- Responde no mesmo idioma da pergunta (PT/EN).\n"
        f"- Texto simples, sem markdown (*, **).\n"
        f"- Se pedirem para adicionar ao carrinho, usa [CART_ADD: ID: QUANTIDADE]\n"
        f"  Exemplo: [CART_ADD: 3: 1] para 1 unidade do produto ID 3.\n"
        f"- Respeita permissões do utilizador.\n"
        f"- Resposta curta e simpática.\n\n"
        f"CONTEXTO:\n{context}\n\n"
        f"PERGUNTA: {user_message}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    # 6. Chamar API com retry
    try:
        response = None
        result = None
        max_attempts = 2  # Reduzido de 3 para 2
        
        for attempt in range(max_attempts):
            start_time = time.time()
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=25)
            elapsed_time = time.time() - start_time
            
            print(f"GEMINI RESPONSE TIME: {elapsed_time:.2f}s | Intents: {intents}")
            
            result = response.json()
            
            if response.status_code == 200:
                break
            
            if response.status_code == 503 and attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            
            break
        
        # 7. Processar resposta
        if response.status_code == 200 and 'candidates' in result:
            try:
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError, TypeError):
                return JsonResponse({'response': "Resposta inesperada do Gemini."}, status=500)
            
            # Processar carrinho
            added_items = []
            matches = re.findall(r'\[CART_ADD:\s*(\d+):\s*(\d+)\]', ai_text)
            cart = request.session.get('cart', {})
            
            if matches:
                ai_text = re.sub(r'\[CART_ADD:\s*\d+:\s*\d+\]', '', ai_text).strip()
                
                for pid_str, qty_str in matches:
                    pid = int(pid_str)
                    qty = int(qty_str)
                    
                    try:
                        product = Product.objects.get(pk=pid, is_available=True)
                        
                        if product.stock is not None and product.stock < qty:
                            if "stock" not in ai_text.lower():
                                ai_text += f"\n\n(Nota: '{product.name}' sem stock suficiente.)"
                            continue
                        
                        pid_key = str(pid)
                        cart[pid_key] = cart.get(pid_key, 0) + qty
                        
                        added_items.append({'id': pid, 'name': product.name, 'quantity': qty})
                    except Product.DoesNotExist:
                        continue
                
                request.session['cart'] = cart
            
            return JsonResponse({
                'response': ai_text,
                'cart_total': sum(cart.values()),
                'added_items': added_items
            })
        
        # 8. Tratar erros
        if response.status_code == 429:
            return JsonResponse({'response': "Limite da API atingido. Aguarda e tenta novamente."})
        
        if response.status_code == 503:
            return JsonResponse({'response': "Servidor Gemini ocupado. Tenta novamente."})
        
        if response.status_code == 403:
            error_msg = result.get('error', {}).get('message', 'API Key recusada.')
            return JsonResponse({'response': f"Erro autenticação (403): {error_msg}"}, status=500)
        
        error_msg = result.get('error', {}).get('message', 'Erro desconhecido.')
        return JsonResponse({'response': f"Erro API ({response.status_code}): {error_msg}"}, status=500)
    
    except requests.exceptions.Timeout:
        return JsonResponse({'response': "Timeout do Gemini."}, status=500)
    
    except requests.exceptions.RequestException as e:
        return JsonResponse({'response': f"Erro ligação: {str(e)}"}, status=500)
    
    except Exception as e:
        return JsonResponse({'response': f"Erro interno: {str(e)}"}, status=500)