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
    context = f"Tu és o 'Barista AI', o assistente inteligente do Bar Escolar. O utilizador atual é um {user.get_user_type_display()}.\n"
    
    # Dados comuns (Menu e Horários)
    products = Product.objects.filter(is_available=True)
    context += "MENU DISPONÍVEL:\n"
    for p in products:
        context += f"- {p.name}: €{p.price} (Categoria: {p.category.name if p.category else 'Geral'})\n"

    # Dados Restritos (Apenas Staff e Admin)
    if user.user_type in ['staff', 'admin']:
        User = get_user_model()
        total_user_balance = User.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
        total_users = User.objects.count()
        students_count = User.objects.filter(user_type='student').count()
        teachers_count = User.objects.filter(user_type='teacher').count()
        staff_count = User.objects.filter(user_type='staff').count()
        admin_count = User.objects.filter(user_type='admin').count()

        context += "\n--- DADOS ADMINISTRATIVOS (CONFIDENCIAIS) ---\n"
        context += f"Saldo da Escola: €{SchoolAccount.objects.get(pk=1).balance}\n"
        context += f"Saldo Agregado dos Utilizadores (total guardado em contas de clientes): €{total_user_balance:.2f}\n"
        context += f"Total de Utilizadores Registados: {total_users} (Alunos: {students_count}, Professores: {teachers_count}, Funcionários: {staff_count}, Admins: {admin_count})\n"
        
        # Produtos em Stock e Previsão de Lucro
        all_products = Product.objects.filter(is_available=True)
        total_stock_cost = sum((p.stock * (p.purchase_price if p.purchase_price is not None else (p.price * Decimal('0.50')))) for p in all_products)
        potential_revenue = sum((p.stock * p.price) for p in all_products)
        potential_profit = potential_revenue - total_stock_cost
        
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

    # 2. Chamar a API do Gemini
    if not GEMINI_API_KEY:
        return JsonResponse({
            'response': f"Olá! Sou o Barista AI. (Configuração: Adiciona a tua GEMINI_API_KEY no settings.py para eu funcionar a sério). Recebi a tua pergunta: '{user_message}'",
            'debug_context': context
        })

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Contexto do Sistema:\n{context}\n\nPergunta do Utilizador: {user_message}\n\nResponde de forma curta, amigável e em Português de Portugal. Se não souberes algo, admite. Respeita estritamente as permissões do utilizador mencionadas no contexto."
            }]
        }]
    }

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        result = response.json()
        
        if 'candidates' in result:
            ai_text = result['candidates'][0]['content']['parts'][0]['text']
            return JsonResponse({'response': ai_text})
        else:
            # Se a API da Google retornar um erro (ex: chave inválida)
            error_msg = result.get('error', {}).get('message', 'Erro desconhecido da API')
            return JsonResponse({'response': f"Erro da Google API: {error_msg}"}, status=500)
            
    except Exception as e:
        return JsonResponse({'response': f"Erro interno: {str(e)}"}, status=500)
