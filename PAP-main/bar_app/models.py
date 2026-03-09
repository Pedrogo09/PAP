"""
Modelos do sistema de gestão do bar escolar
Implementa herança de utilizadores e gestão de pedidos
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime
from django.utils import timezone


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
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    photo = models.ImageField(upload_to='users/', blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    email_verified = models.BooleanField(default=False)
    """Flag usada para saber se o e‑mail já foi confirmado pelo utilizador."""

    def is_priority_user(self):
        """Professores e funcionários têm prioridade"""
        return self.user_type in ['teacher', 'staff', 'admin']
    
    def can_place_order(self):
        """Verifica se pode fazer pedidos"""
        return self.is_active and self.balance >= 0


class Student(models.Model):
    """
    Extensão do modelo User para alunos
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_number = models.CharField(max_length=20, unique=True)
    grade = models.CharField(max_length=10)
    class_name = models.CharField(max_length=10)
    parent_phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_number}"


class Teacher(models.Model):
    """
    Extensão do modelo User para professores
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    employee_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"


class Staff(models.Model):
    """
    Extensão do modelo User para funcionários
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    employee_number = models.CharField(max_length=20, unique=True)
    position = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"


class Category(models.Model):
    """
    Categoria de produtos
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Produto disponível no bar
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    min_stock = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - €{self.price}"
    
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
        ('card', 'Cartão Pré-carregado'),
        ('atm', 'Multibanco'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    notes = models.TextField(blank=True)
    is_priority = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_priority', 'scheduled_date', 'scheduled_time', 'created_at']
    
    def __str__(self):
        return f"Pedido {self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Gerar número de pedido único
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"ORD{timestamp}"
        
        # Definir prioridade baseada no tipo de utilizador
        self.is_priority = self.user.is_priority_user()
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calcula o total do pedido"""
        total = sum((item.subtotal for item in self.items.all()), Decimal('0.00'))
        self.total_amount = total
        self.save()
        return total
    
    def can_be_cancelled(self):
        """Verifica se o pedido pode ser cancelado"""
        return self.status in ['pending', 'confirmed']


class OrderItem(models.Model):
    """
    Item individual de um pedido
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
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
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=200)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
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
                # custo do stock = 50% do preço de venda * quantidade
                cost_per_unit = (self.product.price * Decimal('0.50'))
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
    start_day = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)])
    end_day = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)])
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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

    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, unique=False)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
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
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
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
    school_account = models.ForeignKey(SchoolAccount, on_delete=models.CASCADE, related_name='transactions')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - €{self.amount} - {self.school_account}"
class OrderReview(models.Model):
    """
    Avaliação de um pedido pelo utilizador
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Produto Favorito'
        verbose_name_plural = 'Produtos Favoritos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} gosta de {self.product.name}"
