from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from .models import User, Product, Category, Transaction, StockMovement, SchoolAccount

class MultiUserFinanceTestCase(TestCase):
    def setUp(self):
        # Criar utilizadores de teste
        self.student = User.objects.create_user(
            username='aluno_test', email='aluno@gmail.com', password='password123',
            user_type='student', balance=Decimal('20.00')
        )
        self.staff = User.objects.create_user(
            username='staff_test', email='staff@gmail.com', password='password123',
            user_type='staff', is_staff=True
        )
        
        # Criar categoria e produto
        self.category = Category.objects.create(name='Bebidas')
        self.product = Product.objects.create(
            name='Café', category=self.category, price=Decimal('0.60'), stock=100
        )
        
        # Criar conta da escola
        self.school_account = SchoolAccount.objects.create(pk=1, balance=Decimal('100.00'))

    def test_topup_updates_balance(self):
        """Testar que um carregamento aumenta o saldo do utilizador"""
        initial_balance = self.student.balance
        topup_amount = Decimal('10.00')
        
        Transaction.objects.create(
            user=self.student,
            transaction_type='topup',
            amount=topup_amount,
            description='Carregamento de teste'
        )
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, initial_balance + topup_amount)

    def test_payment_updates_balance(self):
        """Testar que um pagamento diminui o saldo do utilizador"""
        initial_balance = self.student.balance
        payment_amount = Decimal('5.00')
        
        Transaction.objects.create(
            user=self.student,
            transaction_type='payment',
            amount=payment_amount,
            description='Pagamento de teste'
        )
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.balance, initial_balance - payment_amount)

    def test_stock_movement_out_updates_stock(self):
        """Testar que uma saída de stock diminui o stock do produto"""
        initial_stock = self.product.stock
        quantity = 5
        
        StockMovement.objects.create(
            product=self.product,
            movement_type='out',
            quantity=quantity,
            reason='Venda de teste',
            created_by=self.staff
        )
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - quantity)

    def test_staff_restock_updates_school_balance(self):
        """Testar que adição de stock por staff desconta na conta da escola"""
        initial_school_balance = self.school_account.balance
        quantity = 20
        cost_per_unit = self.product.price * Decimal('0.50')
        expected_cost = cost_per_unit * Decimal(quantity)
        
        StockMovement.objects.create(
            product=self.product,
            movement_type='in',
            quantity=quantity,
            reason='Compra de stock',
            created_by=self.staff
        )
        
        self.school_account.refresh_from_db()
        self.assertEqual(self.school_account.balance, initial_school_balance - expected_cost)
