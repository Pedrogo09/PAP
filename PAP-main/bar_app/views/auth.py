from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
from ..models import User

def is_staff_user(user):
    """Função helper para testar se o utilizador é staff"""
    return user.is_staff or user.user_type in ['admin', 'staff']

def login_view(request):
    """Login de utilizador"""
    if request.user.is_authenticated:
        return redirect('bar_app:menu')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Bem-vindo de volta, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'bar_app:menu')
            return redirect(next_url)
        else:
            try:
                u = User.objects.get(username=username)
                if not u.is_active:
                    messages.error(request, 'Conta não activada. Verifique o seu email.')
                else:
                    messages.error(request, 'Nome de utilizador ou palavra-passe incorretos.')
            except User.DoesNotExist:
                messages.error(request, 'Nome de utilizador ou palavra-passe incorretos.')
    
    return render(request, 'bar_app/login.html')

def register(request):
    """Registo de novo utilizador"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user_type = request.POST.get('user_type') or 'student'
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'As palavras-passe não coincidem.')
            return render(request, 'bar_app/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Este nome de utilizador já existe.')
            return render(request, 'bar_app/register.html')
        
        if not email or '@' not in email:
            messages.error(request, 'É necessário fornecer um email válido.')
            return render(request, 'bar_app/register.html')

        if not email.lower().endswith('@gmail.com'):
            messages.error(request, 'O email tem de ser uma conta Google (gmail.com).')
            return render(request, 'bar_app/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está registado.')
            return render(request, 'bar_app/register.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                is_active=False
            )
            
            if user_type in ['staff', 'admin']:
                user.is_staff = True
            if user_type == 'admin':
                user.is_superuser = True
            user.save()

            from ..utils import make_verification_token
            from django.conf import settings
            token = make_verification_token(user)
            
            # Se SITE_URL estiver definido no settings, usá-lo para o host
            if getattr(settings, 'SITE_URL', ''):
                site_url = settings.SITE_URL.rstrip('/')
                path = reverse('bar_app:verify_email', args=[token])
                verify_url = f"{site_url}{path}"
            else:
                verify_url = request.build_absolute_uri(
                    reverse('bar_app:verify_email', args=[token])
                )
            subject = 'Confirme o seu email - Bar Escolar'
            body = (
                f'Olá {user.username},\nclique no link abaixo para activar a sua conta:\n'
                f'{verify_url}\n\nSe não pediu este email, pode ignorá-lo.'
            )
            email_message = EmailMessage(subject, body, to=[user.email])
            email_message.send(fail_silently=True)

            messages.success(request, 'Conta criada! Verifique o seu email para activar a conta.')
            return redirect('bar_app:login')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return render(request, 'bar_app/register.html')
    
    return render(request, 'bar_app/register.html')

def verify_email(request, token):
    """Confirma o email do utilizador a partir do token."""
    from ..utils import check_verification_token
    user = check_verification_token(token)
    if user:
        user.email_verified = True
        user.is_active = True
        user.save()
        messages.success(request, 'Email verificado com sucesso! Já pode iniciar sessão.')
    else:
        messages.error(request, 'Link de verificação inválido ou expirado.')
    return redirect('bar_app:login')

def logout_view(request):
    """Logout do utilizador"""
    auth_logout(request)
    messages.success(request, 'Sessão terminada com sucesso.')
    return redirect('bar_app:home')
