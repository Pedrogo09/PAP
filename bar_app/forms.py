"""
Formulários da aplicação
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from captcha.fields import CaptchaField
from .models import User, Order, Product, Transaction, WeekdayAvailability, Category, OrderReview
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime


class UserRegistrationForm(UserCreationForm):
    """Formulário de registo de utilizador"""
    email = forms.EmailField(required=True)
    captcha = CaptchaField(label="Código de Verificação")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'escalao', 'phone', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    """Formulário de login com captcha"""
    captcha = CaptchaField(label="Código de Verificação")


class OrderForm(forms.ModelForm):
    """Formulário de criação de pedido"""
    
    class Meta:
        model = Order
        fields = ['scheduled_date', 'scheduled_time', 'payment_method', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        scheduled_date = cleaned.get('scheduled_date')
        scheduled_time = cleaned.get('scheduled_time')
        if scheduled_date and scheduled_time:
            now_dt = timezone.localtime()
            today = now_dt.date()
            current_time = now_dt.time()

            # Não permitir datas passadas
            if scheduled_date < today:
                raise ValidationError('A data selecionada já passou.')

            # Se for hoje, hora não pode estar no passado
            if scheduled_date == today and scheduled_time <= current_time:
                raise ValidationError('A hora selecionada já passou.')

            # Verificar disponibilidade para o dia da semana
            weekday = scheduled_date.weekday()  # Monday=0
            avail_qs = WeekdayAvailability.objects.filter(weekday=weekday, is_active=True)
            if not avail_qs.exists():
                raise ValidationError('O bar não está disponível neste dia da semana.')

            # Validar se pelo menos um intervalo cobre a hora solicitada
            ok = False
            for avail in avail_qs:
                if avail.start_time <= scheduled_time <= avail.end_time:
                    ok = True
                    break
            if not ok:
                raise ValidationError('A hora selecionada não está dentro do período de funcionamento.')

        return cleaned


class TopUpForm(forms.ModelForm):
    """Formulário de carregamento de saldo"""
    
    class Meta:
        model = Transaction
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '5', 'step': '0.01', 'class': 'form-control'}),
        }


class ProductForm(forms.ModelForm):
    """Formulário de produto"""
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'purchase_price', 'stock', 'min_stock', 'is_available', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class AddStockForm(forms.Form):
    """Formulário para adicionar stock a um produto"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        label='Categoria',
        required=False,
        empty_label='-- Todas as Categorias --',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_category'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label='Produto',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_product'})
    )
    product_search = forms.CharField(
        label='Pesquisar Produto',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome do produto...',
            'id': 'id_product_search'
        })
    )
    quantity = forms.IntegerField(
        label='Quantidade',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
class OrderReviewForm(forms.ModelForm):
    """Formulário para avaliação do pedido"""
    class Meta:
        model = OrderReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Estrelas") for i in range(1, 6)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Deixe a sua mensagem (opcional)...'}),
        }
