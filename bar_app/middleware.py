"""
Middleware customizado para prevenir conflitos de sessão
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class AdminAccessMiddleware:
    """
    Previne que alunos e professores acedam ao admin acidentalmente
    e mostra mensagem de aviso
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar se está a tentar aceder ao admin
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            # Permitir apenas staff e admins
            if not request.user.is_staff and request.user.user_type not in ['admin', 'staff']:
                messages.warning(
                    request, 
                    'Não tem permissão para aceder à área administrativa. Esta área é apenas para funcionários.'
                )
                return redirect('bar_app:menu')
        
        response = self.get_response(request)
        return response
