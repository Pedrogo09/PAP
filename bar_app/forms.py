"""
Formulários da aplicação
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Order, Product, Transaction, WeekdayAvailability, Category, OrderReview
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime


class UserRegistrationForm(UserCreationForm):
    """Formulário de registo de utilizador"""
    email = forms.EmailField(required=True)
    
    COURSE_CHOICES = [
        ('', 'Selecione o Curso'),
        ('Bombeiro/a', 'Bombeiro/a (Segurança e Prevenção)'),
        ('Auxiliar de Farmácia', 'Auxiliar de Farmácia'),
        ('Auxiliar de Saúde', 'Auxiliar de Saúde'),
        ('Cozinha/Pastelaria', 'Cozinha/Pastelaria (Cozinha e Restauração)'),
        ('Pastelaria/Padaria', 'Pastelaria/Padaria (Cozinha e Restauração)'),
        ('Restaurante/Bar', 'Restaurante/Bar (Cozinha e Restauração)'),
        ('Animação Turística', 'Animação Turística'),
        ('Operações Turísticas', 'Operações Turísticas (Turismo)'),
        ('Produção Aeronáutica', 'Produção Aeronáutica'),
        ('Fabrico Assistido por Computador', 'Fabrico Assistido por Computador (CNC) - (Programação e Maquinação CNC)'),
        ('Mecatrónica', 'Mecatrónica'),
        ('Mecatrónica Automóvel', 'Mecatrónica Automóvel'),
        ('Eletrónica e Automação', 'Eletrónica e Automação (Computadores)'),
        ('Eletrónica e Comunicações', 'Eletrónica e Comunicações (Telecomunicações)'),
        ('Programador/a de Informática', 'Programador/a de Informática (Desenvolvimento de Software)'),
        ('Informática de Gestão', 'Informática de Gestão'),
        ('Gestão de Equipamentos Informáticos', 'Gestão de Equipamentos Informáticos (Sistemas de Computação e Redes)'),
        ('Informática - Instalação e Gestão de Redes', 'Informática - Instalação e Gestão de Redes (Sistemas de Computação e Redes)'),
        ('Design de Comunicação Gráfica', 'Design de Comunicação Gráfica'),
        ('Multimédia', 'Multimédia'),
        ('Gestão', 'Gestão (Gestão e Administração)'),
        ('Cabeleireiro/a', 'Cabeleireiro/a'),
    ]
    
    YEAR_CHOICES = [
        ('', 'Selecione o Ano'),
        ('10', '10º Ano'),
        ('11', '11º Ano'),
        ('12', '12º Ano'),
    ]
    
    course = forms.ChoiceField(
        choices=COURSE_CHOICES,
        required=False,
        label='Curso',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=False,
        label='Ano',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'escalao', 'phone', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar curso e ano obrigatórios apenas para alunos
        if self.data.get('user_type') == 'student':
            self.fields['course'].required = True
            self.fields['year'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        course = cleaned_data.get('course')
        year = cleaned_data.get('year')
        
        # Se for aluno, curso e ano são obrigatórios
        if user_type == 'student':
            if not course:
                self.add_error('course', 'O curso é obrigatório para alunos.')
            if not year:
                self.add_error('year', 'O ano é obrigatório para alunos.')
            
            # Gerar turma no formato CURSO-ANO (ex: 10PI, 11PI, 12PI)
            if course and year:
                # Extrair sigla do curso (primeiras letras ou abreviação)
                course_abbr = self._get_course_abbreviation(course)
                cleaned_data['turma'] = f"{year}{course_abbr}"
        
        return cleaned_data
    
    def _get_course_abbreviation(self, course):
        """Retorna abreviação do curso para formar a turma"""
        abbreviations = {
            'Bombeiro/a': 'BP',
            'Auxiliar de Farmácia': 'AF',
            'Auxiliar de Saúde': 'AS',
            'Cozinha/Pastelaria': 'CP',
            'Pastelaria/Padaria': 'PP',
            'Restaurante/Bar': 'RB',
            'Animação Turística': 'AT',
            'Operações Turísticas': 'OT',
            'Produção Aeronáutica': 'PA',
            'Fabrico Assistido por Computador': 'CNC',
            'Mecatrónica': 'MEC',
            'Mecatrónica Automóvel': 'MA',
            'Eletrónica e Automação': 'EA',
            'Eletrónica e Comunicações': 'EC',
            'Programador/a de Informática': 'PI',
            'Informática de Gestão': 'IG',
            'Gestão de Equipamentos Informáticos': 'GEI',
            'Informática - Instalação e Gestão de Redes': 'IGR',
            'Design de Comunicação Gráfica': 'DCG',
            'Multimédia': 'MM',
            'Gestão': 'GES',
            'Cabeleireiro/a': 'CB',
        }
        return abbreviations.get(course, 'GEN')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.turma = self.cleaned_data.get('turma', '')
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Formulário de login"""
    pass


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
