"""
Modelos do sistema de gestão do bar escolar
Implementa herança de utilizadores e gestão de pedidos
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime
import random
import string
from django.utils import timezone


ESCALAO_CHOICES = (
    ('none', 'Nenhum'),
    ('A', 'Escalão A'),
    ('B', 'Escalão B'),
    ('C', 'Escalão C'),
)


class User(AbstractUser):
    """
    Modelo base de utilizador com herança
    """
    USER_TYPE_CHOICES = (
        ('student', 'Aluno'),
        ('teacher', 'Professor'),
        ('staff', 'Funcionário'),
        ('admin', 'Administrador'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student', verbose_name='Tipo de Utilizador')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Telemóvel')
    photo = models.ImageField(upload_to='users/', blank=True, null=True, verbose_name='Foto')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Saldo')
    loyalty_points = models.IntegerField(default=0, help_text="Pontos de fidelidade (1€ = 1 ponto)", verbose_name='Pontos de Fidelidade')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    escalao = models.CharField(max_length=10, choices=ESCALAO_CHOICES, default='none', verbose_name='Escalão ASE')
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.'
    )
    
    class Meta:
        verbose_name = 'Utilizador'
        verbose_name_plural = 'Utilizadores'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"
    
    @property
    def logo_avatar(self):
        return "/static/images/logo.png"

    email_verified = models.BooleanField(default=False)
    """Flag usada para saber se o e‑mail já foi confirmado pelo utilizador."""

    def is_priority_user(self):
        """Professores e funcionários têm prioridade"""
        return self.user_type in ['teacher', 'staff', 'admin']
    
    @property
    def discount_multiplier(self):
        """
        Retorna o multiplicador de preço com base no escalão (apenas para alunos)
        Escalão A: 75% desconto (paga 25%)
        Escalão B: 50% desconto (paga 50%)
        Escalão C: 25% desconto (paga 75%)
        Nenhum: 0% desconto (paga 100%)
        """
        if self.user_type != 'student':
            return Decimal('1.0')
        
        mapping = {
            'A': Decimal('0.25'),
            'B': Decimal('0.50'),
            'C': Decimal('0.75'),
            'none': Decimal('1.0'),
        }
        return mapping.get(self.escalao, Decimal('1.0'))
    
    def can_place_order(self):
        """Verifica se pode fazer pedidos"""
        return self.is_active and self.balance >= 0


class Student(models.Model):
    """
    Extensão do modelo User para alunos
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name='Utilizador')
    student_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Aluno')
    grade = models.CharField(max_length=10, verbose_name='Ano/Grau')
    class_name = models.CharField(max_length=10, verbose_name='Turma')
    parent_phone = models.CharField(max_length=15, blank=True, verbose_name='Telemóvel do Encarregado')
    
    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_number}"


class Teacher(models.Model):
    """
    Extensão do modelo User para professores
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name='Utilizador')
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Funcionário')
    department = models.CharField(max_length=100, verbose_name='Departamento')
    
    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'

    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"


class Staff(models.Model):
    """
    Extensão do modelo User para funcionários
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name='Utilizador')
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='Número de Funcionário')
    position = models.CharField(max_length=100, verbose_name='Cargo/Posição')
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"


class Category(models.Model):
    """
    Categoria de produtos
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Imagem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Produto disponível no bar
    """
    name = models.CharField(max_length=200, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    allergens = models.CharField(max_length=200, blank=True, help_text="Ex: Glúten, Lactose, Frutos Secos", verbose_name='Alergéneos')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Categoria')
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name='Preço de Venda')
    purchase_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))], verbose_name='Preço de Custo', help_text="Preço pago pelo bar ao fornecedor")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Imagem')
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Stock Atual')
    min_stock = models.IntegerField(default=10, validators=[MinValueValidator(0)], verbose_name='Stock Mínimo')
    expiration_date = models.DateField(blank=True, null=True, help_text="Data de validade do lote atual", verbose_name='Data de Validade')
    is_available = models.BooleanField(default=True, verbose_name='Disponível')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - €{self.price}"
    
    def get_price_for_user(self, user):
        """Retorna o preço final para o utilizador, aplicando descontos de escalão"""
        if not user or not user.is_authenticated:
            return self.price
        
        discounted_price = self.price * user.discount_multiplier
        return discounted_price.quantize(Decimal('0.01'))
    
    def is_in_stock(self):
        """Verifica se há stock disponível"""
        return self.stock > 0
    
    def needs_restock(self):
        """Verifica se precisa de reabastecimento"""
        return self.stock <= self.min_stock


class Order(models.Model):
    """
    Pedido realizado por um utilizador
    """
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'Em Preparação'),
        ('ready', 'Pronto'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Cartão Escolar'),
        ('atm', 'Multibanco'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Utilizador')
    order_number = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Número do Pedido')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Estado')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, verbose_name='Método de Pagamento')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Montante Total')
    scheduled_date = models.DateField(verbose_name='Data Agendada')
    scheduled_time = models.TimeField(verbose_name='Hora Agendada')
    notes = models.TextField(blank=True, verbose_name='Notas')
    is_priority = models.BooleanField(default=False, verbose_name='Prioritário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-is_priority', 'scheduled_date', 'scheduled_time', 'created_at']
    
    def __str__(self):
        return f"Pedido {self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Gerar número de pedido único curto (Ex: ORD-A1B2C)
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            self.order_number = f"ORD-{random_str}"
        
        # Definir prioridade baseada no tipo de utilizador
        self.is_priority = self.user.is_priority_user()
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calcula o total do pedido"""
        total = sum((item.subtotal for item in self.items.all()), Decimal('0.00'))
        self.total_amount = total
        self.save()
        return total
    
    def get_cancellation_info(self):
        """
        Retorna (pode_cancelar, precisa_multa, valor_multa)
        """
        if self.status not in ['pending', 'confirmed']:
            return False, False, Decimal('0.00')
        
        # Combinar data e hora agendada
        from django.utils import timezone
        import datetime
        scheduled_dt = timezone.make_aware(datetime.datetime.combine(self.scheduled_date, self.scheduled_time))
        now = timezone.localtime()
        
        # Diferença em minutos
        diff = (scheduled_dt - now).total_seconds() / 60
        
        if diff < 0: # Já passou da hora
            return False, False, Decimal('0.00')
        
        needs_fine = diff < 15
        fine_amount = self.total_amount * Decimal('0.10') if needs_fine else Decimal('0.00')
        
        return True, needs_fine, fine_amount

    def can_be_cancelled(self):
        """Verifica se o pedido pode ser cancelado (apenas boolean para compatibilidade)"""
        can, _, _ = self.get_cancellation_info()
        return can


class OrderItem(models.Model):
    """
    Item individual de um pedido
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Produto')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Quantidade')
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Preço Unitário')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')
    
    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Itens de Pedido'
        ordering = ['product__name']
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal
        # garantir que o preço unitário exista e usar Decimal para o subtotal
        if not self.unit_price:
            self.unit_price = self.product.price
        self.subtotal = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)
        # Atualizar total do pedido
        self.order.calculate_total()


class Transaction(models.Model):
    """
    Transação financeira (carregamentos e pagamentos)
    """
    TRANSACTION_TYPE_CHOICES = (
        ('topup', 'Carregamento'),
        ('payment', 'Pagamento'),
        ('refund', 'Reembolso'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name='Utilizador')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name='Tipo de Transação')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montante')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='Pedido')
    description = models.CharField(max_length=200, verbose_name='Descrição')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Realizada em')
    
    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - €{self.amount} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Atualizar saldo do utilizador
        if self.transaction_type == 'topup':
            self.user.balance += self.amount
        elif self.transaction_type == 'payment':
            self.user.balance -= self.amount
        elif self.transaction_type == 'refund':
            # reembolsos devolvem o montante ao utilizador
            self.user.balance += self.amount
        
        self.user.save()
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    """
    Movimento de stock (entradas e saídas)
    """
    MOVEMENT_TYPE_CHOICES = (
        ('in', 'Entrada'),
        ('out', 'Saída'),
        ('adjustment', 'Ajuste'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements', verbose_name='Produto')
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPE_CHOICES, verbose_name='Tipo de Movimento')
    quantity = models.IntegerField(verbose_name='Quantidade')
    reason = models.CharField(max_length=200, verbose_name='Motivo')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Pedido')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Criado por')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Movimento de Stock'
        verbose_name_plural = 'Movimentos de Stock'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Atualizar stock do produto
        if self.movement_type == 'in':
            self.product.stock += self.quantity
        elif self.movement_type == 'out':
            self.product.stock -= self.quantity
        elif self.movement_type == 'adjustment':
            self.product.stock = self.quantity
        
        self.product.save()
        super().save(*args, **kwargs)

        # Se for entrada de stock feita por staff/admin, descontar custo da conta da escola
        # MAS: não fazer se já foi processado via admin (flag _admin_processed)
        try:
            from django.db import transaction as db_tx
            if self.movement_type == 'in' and self.created_by and self.created_by.is_staff and not getattr(self, '_admin_processed', False):
                # custo do stock = purchase_price ou 50% do preço de venda
                cost_per_unit = self.product.purchase_price if self.product.purchase_price is not None else (self.product.price * Decimal('0.50'))
                total_cost = (cost_per_unit * Decimal(self.quantity)).quantize(Decimal('0.01'))

                # Modelo singleton da conta da escola
                sa, created = SchoolAccount.objects.get_or_create(pk=1, defaults={'balance': Decimal('0.00')})
                # Debitar custo
                sa.balance -= total_cost
                sa.save()

                # Registar transacção da escola
                SchoolTransaction.objects.create(
                    school_account=sa,
                    movement_type='expense',
                    amount=total_cost,
                    description=f'Compra stock: {self.product.name} x{self.quantity}',
                    created_by=self.created_by
                )
        except Exception:
            # Não falhar a operação principal por causa de problemas contabilísticos
            pass


class BarSchedule(models.Model):
    """
    Horários de funcionamento do bar por intervalo de dias
    """
    start_day = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)], verbose_name='Dia Inicial (0-6)')
    end_day = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)], verbose_name='Dia Final (0-6)')
    opening_time = models.TimeField(verbose_name='Hora de Abertura')
    closing_time = models.TimeField(verbose_name='Hora de Fecho')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Horário do Bar'
        verbose_name_plural = 'Horários do Bar'
        ordering = ['start_day']

    def __str__(self):
        return f"Dias {self.start_day}-{self.end_day}: {self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')}"


class WeekdayAvailability(models.Model):
    """Disponibilidade por dia da semana (segunda..domingo) com intervalo de horas."""
    WEEKDAY_CHOICES = (
        (0, 'Segunda'),
        (1, 'Terça'),
        (2, 'Quarta'),
        (3, 'Quinta'),
        (4, 'Sexta'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    )

    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, unique=False, verbose_name='Dia da Semana')
    start_time = models.TimeField(verbose_name='Hora de Início')
    end_time = models.TimeField(verbose_name='Hora de Fim')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Disponibilidade por Dia'
        verbose_name_plural = 'Disponibilidades por Dia'
        ordering = ['weekday', 'start_time']

    def __str__(self):
        day = dict(self.WEEKDAY_CHOICES).get(self.weekday, str(self.weekday))
        return f"{day}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class SchoolAccount(models.Model):
    """Conta financeira da escola (saldo usado para compras de stock)."""
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Saldo')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta da Escola'
        verbose_name_plural = 'Contas da Escola'

    def __str__(self):
        return f"Conta Escola - €{self.balance}"


class SchoolTransaction(models.Model):
    MOVEMENT_CHOICES = (
        ('income', 'Entrada'),
        ('expense', 'Despesa'),
    )
    school_account = models.ForeignKey(SchoolAccount, on_delete=models.CASCADE, related_name='transactions', verbose_name='Conta da Escola')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES, verbose_name='Tipo de Movimento')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Montante')
    description = models.CharField(max_length=255, verbose_name='Descrição')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Criado por')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Transação da Escola'
        verbose_name_plural = 'Transações da Escola'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - €{self.amount} - {self.school_account}"
class OrderReview(models.Model):
    """
    Avaliação de um pedido pelo utilizador
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review', verbose_name='Pedido')
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], verbose_name='Avaliação (0-5)')
    comment = models.TextField(blank=True, verbose_name='Comentário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Avaliação de Pedido'
        verbose_name_plural = 'Avaliações de Pedidos'
    
    def __str__(self):
        return f"Avaliação {self.rating}/5 - Pedido {self.order.order_number}"

class FavoriteProduct(models.Model):
    """
    Produtos marcados como favoritos pelo utilizador
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='Utilizador')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='Produto')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Marcado em')

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Produto Favorito'
        verbose_name_plural = 'Produtos Favoritos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} gosta de {self.product.name}"
