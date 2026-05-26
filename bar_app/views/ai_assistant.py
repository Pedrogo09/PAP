import json
import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Sum, F
from ..models import Product, Order, Transaction, Category, SchoolAccount
from django.contrib.auth import get_user_model
from decimal import Decimal

GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', '')

@login_required
def ai_chat_response(request):
    """View que processa a pergunta do utilizador e responde usando IA com contexto do site"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
    except:
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    # 1. Construir o Contexto baseado no Tipo de Utilizador
    user = request.user
<<<<<<< HEAD
    context = f"Tu és o 'Barista AI', o assistente inteligente do Bar Escolar. O utilizador atual é um {user.get_user_type_display()}.\n"
    
    # Dados comuns (Menu e Horários)
    products = Product.objects.filter(is_available=True)
    context += "MENU DISPONÍVEL:\n"
    for p in products:
        context += f"- {p.name}: €{p.price} (Categoria: {p.category.name if p.category else 'Geral'})\n"
=======
    user_type_en = {
        'admin': 'Administrator',
        'staff': 'Staff / Bar Employee',
        'teacher': 'Teacher',
        'student': 'Student'
    }.get(user.user_type, 'User')
    
    context = (
        f"Tu és o 'Barista AI', o assistente inteligente do Bar Escolar / You are the 'Barista AI', the smart assistant of the School Bar.\n"
        f"O utilizador atual é um / The current user is a: {user.get_user_type_display()} ({user_type_en}).\n"
    )
    
    # Dados comuns (Menu e Horários)
    products = Product.objects.filter(is_available=True)
    context += "MENU DISPONÍVEL / AVAILABLE MENU:\n"
    for p in products:
        context += f"- ID: {p.id} | {p.name}: €{p.price} (Categoria/Category: {p.category.name if p.category else 'Geral/General'})\n"
>>>>>>> c69d373 (Logo e IA)

    # Dados Restritos (Apenas Staff e Admin)
    if user.user_type in ['staff', 'admin']:
        User = get_user_model()
        total_user_balance = User.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
        total_users = User.objects.count()
        students_count = User.objects.filter(user_type='student').count()
        teachers_count = User.objects.filter(user_type='teacher').count()
        staff_count = User.objects.filter(user_type='staff').count()
        admin_count = User.objects.filter(user_type='admin').count()

<<<<<<< HEAD
        context += "\n--- DADOS ADMINISTRATIVOS (CONFIDENCIAIS) ---\n"
        context += f"Saldo da Escola: €{SchoolAccount.objects.get(pk=1).balance}\n"
        context += f"Saldo Agregado dos Utilizadores (total guardado em contas de clientes): €{total_user_balance:.2f}\n"
        context += f"Total de Utilizadores Registados: {total_users} (Alunos: {students_count}, Professores: {teachers_count}, Funcionários: {staff_count}, Admins: {admin_count})\n"
=======
        context += "\n--- DADOS ADMINISTRATIVOS (CONFIDENCIAIS) / ADMINISTRATIVE DATA (CONFIDENTIAL) ---\n"
        context += f"Saldo da Escola / School Balance: €{SchoolAccount.objects.get(pk=1).balance}\n"
        context += f"Saldo Agregado dos Utilizadores / Aggregated User Balance: €{total_user_balance:.2f}\n"
        context += f"Total de Utilizadores Registados / Total Registered Users: {total_users} (Alunos/Students: {students_count}, Professores/Teachers: {teachers_count}, Funcionários/Staff: {staff_count}, Admins: {admin_count})\n"
>>>>>>> c69d373 (Logo e IA)
        
        # Produtos em Stock e Previsão de Lucro
        all_products = Product.objects.filter(is_available=True)
        total_stock_cost = sum((p.stock * (p.purchase_price if p.purchase_price is not None else (p.price * Decimal('0.50')))) for p in all_products)
        potential_revenue = sum((p.stock * p.price) for p in all_products)
        potential_profit = potential_revenue - total_stock_cost
        
<<<<<<< HEAD
        context += f"Custo Total do Stock Atual: €{total_stock_cost:.2f}\n"
        context += f"Receita Potencial se vender tudo: €{potential_revenue:.2f}\n"
        context += f"Lucro Potencial Esperado: €{potential_profit:.2f}\n\n"
        
        low_stock = Product.objects.filter(stock__lte=F('min_stock'))
        context += "PRODUTOS COM STOCK BAIXO:\n"
        for lp in low_stock:
            context += f"- {lp.name}: Restam {lp.stock} unidades (Mínimo: {lp.min_stock})\n"
            
        pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
        context += f"Pedidos Pendentes: {pending_orders}\n"
        
        context += "\nLISTA COMPLETA DE PRODUTOS E STOCK:\n"
        for p in all_products:
            custo = p.purchase_price if p.purchase_price else (p.price * Decimal('0.50'))
            context += f"- {p.name}: Stock={p.stock}, Custo=€{custo:.2f}, Preço Venda=€{p.price:.2f}\n"
    else:
        context += "\nNota: Não tens acesso a dados de stock exatos ou financeiros. Se o utilizador perguntar, diz que não tens permissão.\n"
=======
        context += f"Custo Total do Stock / Total Stock Cost: €{total_stock_cost:.2f}\n"
        context += f"Receita Potencial / Potential Revenue: €{potential_revenue:.2f}\n"
        context += f"Lucro Potencial Esperado / Expected Potential Profit: €{potential_profit:.2f}\n\n"
        
        low_stock = Product.objects.filter(stock__lte=F('min_stock'))
        context += "PRODUTOS COM STOCK BAIXO / LOW STOCK PRODUCTS:\n"
        for lp in low_stock:
            context += f"- {lp.name}: Restam / Remaining: {lp.stock} (Mínimo / Min: {lp.min_stock})\n"
            
        pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
        context += f"Pedidos Pendentes / Pending Orders: {pending_orders}\n"
        
        context += "\nLISTA COMPLETA DE PRODUTOS E STOCK / COMPLETE PRODUCT AND STOCK LIST:\n"
        for p in all_products:
            custo = p.purchase_price if p.purchase_price else (p.price * Decimal('0.50'))
            context += f"- {p.name}: Stock={p.stock}, Custo/Cost=€{custo:.2f}, Preço Venda/Selling Price=€{p.price:.2f}\n"
    else:
        context += (
            "\nNota: Não tens acesso a dados de stock exatos ou financeiros. Se o utilizador perguntar, diz que não tens permissão.\n"
            "Note: You do not have access to exact stock or financial data. If the user asks, say you do not have permission.\n"
        )
>>>>>>> c69d373 (Logo e IA)

    # 2. Chamar a API do Gemini
    if not GEMINI_API_KEY:
        return JsonResponse({
            'response': f"Olá! Sou o Barista AI. (Configuração: Adiciona a tua GEMINI_API_KEY no settings.py para eu funcionar a sério). Recebi a tua pergunta: '{user_message}'",
            'debug_context': context
        })

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
<<<<<<< HEAD
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Contexto do Sistema:\n{context}\n\nPergunta do Utilizador: {user_message}\n\nResponde de forma curta, amigável e em Português de Portugal. Se não souberes algo, admite. Respeita estritamente as permissões do utilizador mencionadas no contexto."
=======
    prompt = (
        f"REGRAS DE RESPOSTA:\n"
        f"- Responde ESTRITAMENTE no mesmo idioma em que a pergunta foi feita. Se o utilizador perguntar em inglês (como 'hello', 'hi', 'how are you', 'any suggestions', 'I dont understand'), deves obrigatoriamente responder em inglês (English). Se perguntar em português, responde em português.\n"
        f"- Responde APENAS em texto simples. NUNCA uses formatação markdown (como asteriscos '*' ou '**' para criar listas ou negrito). Se precisares de destacar algo ou listar, usa letras normais, parágrafos ou hífens normais (-).\n"
        f"- Se o utilizador pedir para adicionar produtos ao carrinho (ex: 'mete no carrinho café e compal', 'adiciona um bolo', 'add a coffee to the cart', etc.), deves obrigatoriamente identificar os IDs correspondentes na lista de produtos e adicionar no FINAL da tua resposta uma linha separada contendo '[CART_ADD: ID: QUANTIDADE]' para cada produto. Exemplo se ele pedir 1 café (ID 3) e 2 sumos (ID 5), escreve no fim da resposta: '[CART_ADD: 3: 1]' e '[CART_ADD: 5: 2]' em linhas novas. Não adiciones tags de produtos que não estejam listados ou disponíveis no menu.\n"
        f"- Responde de forma curta, simpática e amigável.\n"
        f"- Respeita estritamente as permissões do tipo de utilizador.\n"
        f"- Traduz o Contexto do Sistema para inglês se responderes em inglês.\n"
        f"- Se não souberes algo, admite.\n\n"
        f"CONTEXTO DO SISTEMA:\n{context}\n\n"
        f"PERGUNTA DO UTILIZADOR: {user_message}"
    )

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
>>>>>>> c69d373 (Logo e IA)
            }]
        }]
    }

    try:
<<<<<<< HEAD
        response = requests.post(api_url, json=payload, timeout=10)
=======
        response = requests.post(api_url, json=payload, timeout=25)
        print(f"[DEBUG GEMINI] Status Code: {response.status_code}")
        print(f"[DEBUG GEMINI] Response Text: {response.text}")
>>>>>>> c69d373 (Logo e IA)
        result = response.json()
        
        if 'candidates' in result:
            ai_text = result['candidates'][0]['content']['parts'][0]['text']
<<<<<<< HEAD
            return JsonResponse({'response': ai_text})
        else:
            # Se a API da Google retornar um erro (ex: chave inválida)
            error_msg = result.get('error', {}).get('message', 'Erro desconhecido da API')
            return JsonResponse({'response': f"Erro da Google API: {error_msg}"}, status=500)
=======
            
            # --- PROCESSAR ADIÇÃO AO CARRINHO ---
            import re
            added_items = []
            matches = re.findall(r'\[CART_ADD:\s*(\d+):\s*(\d+)\]', ai_text)
            
            # Obter o carrinho da sessão atual
            cart = request.session.get('cart', {})
            
            if matches:
                # Limpar as tags técnicas da resposta para que o utilizador não as veja no chat
                ai_text = re.sub(r'\[CART_ADD:\s*\d+:\s*\d+\]', '', ai_text).strip()
                
                for pid_str, qty_str in matches:
                    pid = int(pid_str)
                    qty = int(qty_str)
                    try:
                        product = Product.objects.get(pk=pid, is_available=True)
                        # Verificar stock
                        if product.stock is not None and product.stock < qty:
                            if "stock" not in ai_text.lower():
                                ai_text += f"\n\n(Nota: O produto '{product.name}' está sem stock suficiente de momento.)"
                            continue
                            
                        pid_key = str(pid)
                        if pid_key in cart:
                            cart[pid_key] += qty
                        else:
                            cart[pid_key] = qty
                            
                        added_items.append({
                            'id': pid,
                            'name': product.name,
                            'quantity': qty
                        })
                    except Product.DoesNotExist:
                        continue
                
                # Salvar carrinho de volta na sessão
                request.session['cart'] = cart
                
            total_items = sum(cart.values())
            # ------------------------------------
            
            return JsonResponse({
                'response': ai_text,
                'cart_total': total_items,
                'added_items': added_items
            })
        else:
            # Se for um erro de limite de quota (Rate Limit / Quota Exceeded)
            if response.status_code == 429:
                return JsonResponse({
                    'response': f"Desculpa! O Barista AI recebeu demasiadas perguntas seguidas (limite de quota gratuita do Gemini atingido). Por favor, aguarda cerca de 30 segundos e tenta de novo!\n\n[Debug: Status {response.status_code}]"
                })
            
            # Se a API da Google retornar outro erro (ex: chave inválida)
            error_msg = result.get('error', {}).get('message', 'Erro desconhecido da API')
            return JsonResponse({'response': f"Erro da Google API (Status {response.status_code}): {error_msg}"}, status=500)
>>>>>>> c69d373 (Logo e IA)
            
    except Exception as e:
        return JsonResponse({'response': f"Erro interno: {str(e)}"}, status=500)
