from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout as auth_logout, authenticate, login as auth_login
from django.contrib.auth.decorators import user_passes_test
from ..models import User

def is_staff_user(user):
    """Função helper para testar se o utilizador é staff"""
    return user.is_staff or user.user_type in ['admin', 'staff']

def login_view(request):
    """Login de utilizador"""
    if request.user.is_authenticated:
        return redirect('bar_app:menu')
    
    from ..forms import LoginForm
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Marcar na sessão se o utilizador era admin antes do logout
            if is_staff_user(user):
                request.session['was_admin'] = True
            
            messages.success(request, f'Bem-vindo de volta, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'bar_app:menu')
            return redirect(next_url)
        else:
            try:
                u = User.objects.get(username=request.POST.get('username'))
                if not u.is_active:
                    messages.error(request, 'Conta não activada. Verifique o seu email.')
                else:
                    messages.error(request, 'Nome de utilizador ou palavra-passe incorretos.')
            except User.DoesNotExist:
                messages.error(request, 'Nome de utilizador ou palavra-passe incorretos.')
    else:
        form = LoginForm()
    
    return render(request, 'bar_app/login.html', {'form': form})

def register(request):
    """Registo de novo utilizador"""
    from ..forms import UserRegistrationForm
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'bar_app/register.html', {'form': form})
        
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        
        # Verificações adicionais de email
        if not email.lower().endswith('@gmail.com'):
            messages.error(request, 'O email tem de ser uma conta Google (gmail.com).')
            return render(request, 'bar_app/register.html', {'form': form})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está registado.')
            return render(request, 'bar_app/register.html')
        
        try:
            user = form.save(commit=False)
            user.is_active = False
            
            # NUNCA permitir criar staff/admin via registo público
            # Apenas superuser pode promover utilizadores a staff/admin via Django Admin
            user.is_staff = False
            user.is_superuser = False
            user.save()

            from ..utils import make_verification_token
            token = make_verification_token(user)
            verify_url = request.build_absolute_uri(
                reverse('bar_app:verify_email', args=[token])
            )
            subject = 'Confirme o seu email - Bar Escolar'
            body = (
                f'Olá {user.username},\nclique no link abaixo para activar a sua conta:\n'
                f'{verify_url}\n\nSe não pediu este email, pode ignorá-lo.'
            )
            email_message = EmailMessage(subject, body, to=[user.email])
            email_message.send(fail_silently=False)

            messages.success(request, 'Conta criada! Verifique o seu email para activar a conta.')
            return redirect('bar_app:login')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return render(request, 'bar_app/register.html', {'form': form})
    else:
        form = UserRegistrationForm()
    
    return render(request, 'bar_app/register.html', {'form': form})

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
    # Marcar na sessão se o utilizador era admin antes do logout
    if is_staff_user(request.user):
        request.session['was_admin'] = True
    
    auth_logout(request)
    messages.success(request, 'Sessão terminada com sucesso.')
    return redirect('bar_app:home')

@login_required
@user_passes_test(is_staff_user)
def admin_register(request):
    """Registo de novo utilizador (apenas admin)"""
    from ..forms import UserRegistrationForm
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'bar_app/register.html', {'form': form, 'admin_mode': True})
        
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        
        # Verificações adicionais de email
        if not email.lower().endswith('@gmail.com'):
            messages.error(request, 'O email tem de ser uma conta Google (gmail.com).')
            return render(request, 'bar_app/register.html', {'form': form, 'admin_mode': True})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está registado.')
            return render(request, 'bar_app/register.html', {'form': form, 'admin_mode': True})
        
        try:
            user = form.save(commit=False)
            user.is_active = True  # Admin pode criar contas ativas diretamente
            user.email_verified = True
            
            # Admin pode definir se é staff ou não
            if user.user_type == 'staff':
                user.is_staff = True
            else:
                user.is_staff = False
            user.is_superuser = False
            user.save()

            messages.success(request, f'Conta criada com sucesso para {user.get_full_name() or user.username}!')
            return redirect('bar_app:dashboard')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return render(request, 'bar_app/register.html', {'form': form, 'admin_mode': True})
    else:
        form = UserRegistrationForm()
    
    return render(request, 'bar_app/register.html', {'form': form, 'admin_mode': True})
