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

class UserProfileForm(forms.ModelForm):
    """Formulário para edição do perfil do utilizador e seleção de alérgenos"""
    ALLERGEN_CHOICES = [
        ('Glúten', 'Glúten'),
        ('Lactose', 'Lactose / Laticínios'),
        ('Frutos Secos', 'Frutos Secos (nozes, amêndoas, etc.)'),
        ('Ovos', 'Ovos'),
        ('Amendoins', 'Amendoins'),
        ('Soja', 'Soja'),
        ('Peixe', 'Peixe'),
    ]
    
    COUNTRY_CHOICES = [
        ('+351', '🇵🇹 Portugal (+351)'),
        ('+34', '🇪🇸 Espanha (+34)'),
        ('+33', '🇫🇷 França (+33)'),
        ('+44', '🇬🇧 Reino Unido (+44)'),
        ('+49', '🇩🇪 Alemanha (+49)'),
        ('+39', '🇮🇹 Itália (+39)'),
        ('+31', '🇳🇱 Holanda (+31)'),
        ('+32', '🇧🇪 Bélgica (+32)'),
        ('+41', '🇨🇭 Suíça (+41)'),
        ('+352', '🇱🇺 Luxemburgo (+352)'),
    ]
    
    country_code = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        label='Código do País',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    selected_allergens = forms.MultipleChoiceField(
        choices=ALLERGEN_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="As minhas restrições / alérgenos"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 912345678', 'pattern': '[0-9]*', 'inputmode': 'numeric'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.allergens:
            self.fields['selected_allergens'].initial = [a.strip() for a in self.instance.allergens.split(',') if a.strip()]
        
        # Extract country code from existing phone number
        if self.instance and self.instance.phone:
            phone = self.instance.phone.strip()
            for code, _ in self.COUNTRY_CHOICES:
                if phone.startswith(code):
                    self.fields['country_code'].initial = code
                    self.fields['phone'].initial = phone[len(code):].strip()
                    break
            else:
                # If no country code found, assume Portugal
                if phone.startswith('+'):
                    self.fields['phone'].initial = phone[1:].strip()
                else:
                    self.fields['phone'].initial = phone
                self.fields['country_code'].initial = '+351'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            # Only allow digits
            if not phone.isdigit():
                raise forms.ValidationError('O número de telefone só pode conter dígitos.')
            # Validate length (9 digits for Portugal, adjust as needed)
            if len(phone) < 9 or len(phone) > 15:
                raise forms.ValidationError('O número de telefone deve ter entre 9 e 15 dígitos.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        selected = self.cleaned_data.get('selected_allergens', [])
        user.allergens = ", ".join(selected)
        
        # Combine country code and phone number
        country_code = self.cleaned_data.get('country_code', '+351')
        phone = self.cleaned_data.get('phone', '')
        if phone:
            user.phone = f"{country_code}{phone}"
        else:
            user.phone = ''
        
        if commit:
            user.save()
        return user
