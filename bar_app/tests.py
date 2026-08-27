from django.test import TestCase, Client
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import User, Product, Category, Transaction, StockMovement, SchoolAccount, Order, OrderItem
import json
import threading

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

    def test_user_cannot_access_other_users_order(self):
        """Verificar que o modelo Order tem relação correta com user"""
        student2 = User.objects.create_user(
            username='aluno2', email='aluno2@gmail.com', password='pass123',
            user_type='student', balance=Decimal('30.00')
        )
        
        order = Order.objects.create(
            user=self.student,
            order_number='TEST-001',
            status='pending',
            payment_method='card',
            total_amount=Decimal('5.00'),
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time()
        )
        
        # Verificar que o pedido pertence ao student
        self.assertEqual(order.user, self.student)
        
        # Tentar buscar pedido de outro utilizador deve retornar None
        order_from_student2 = Order.objects.filter(pk=order.pk, user=student2).first()
        self.assertIsNone(order_from_student2)

    def test_registration_security(self):
        """Verificar que utilizadores criados via registo não são staff por defeito"""
        user = User.objects.create_user(
            username='testuser',
            email='test@gmail.com',
            password='password123',
            user_type='student'
        )
        
        # Por defeito, não deve ser staff
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_insufficient_stock_detection(self):
        """Verificar deteção de stock insuficiente"""
        self.product.stock = 0
        self.product.save()
        
        self.assertEqual(self.product.stock, 0)
        self.assertFalse(self.product.is_in_stock())

    def test_insufficient_balance_detection(self):
        """Verificar deteção de saldo insuficiente"""
        self.student.balance = Decimal('0.00')
        self.student.save()
        
        self.assertEqual(self.student.balance, Decimal('0.00'))
        self.assertFalse(self.student.can_place_order())


class QRCodeSystemTestCase(TestCase):
    """Testes para o sistema de QR Code de levantamento de pedidos"""
    
    def setUp(self):
        # Criar utilizadores
        self.student = User.objects.create_user(
            username='aluno_qr', email='aluno_qr@gmail.com', password='password123',
            user_type='student', balance=Decimal('20.00'), turma='12PI'
        )
        self.teacher = User.objects.create_user(
            username='professor_qr', email='prof_qr@gmail.com', password='password123',
            user_type='teacher'
        )
        self.staff = User.objects.create_user(
            username='staff_qr', email='staff_qr@gmail.com', password='password123',
            user_type='staff', is_staff=True
        )
        
        # Criar categoria e produto
        self.category = Category.objects.create(name='Bebidas')
        self.product = Product.objects.create(
            name='Café', category=self.category, price=Decimal('0.60'), stock=100
        )
        
        # Criar pedido com QR token
        self.order = Order.objects.create(
            user=self.student,
            status='ready',
            payment_method='card',
            total_amount=Decimal('1.20'),
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time()
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('0.60'),
            subtotal=Decimal('1.20')
        )
        
        self.client = Client()
    
    def test_order_creates_qr_token(self):
        """Testar que criação de pedido gera token QR válido"""
        order = Order.objects.get(pk=self.order.pk)
        self.assertIsNotNone(order.qr_token)
        self.assertTrue(len(order.qr_token) > 20)
    
    def test_two_orders_have_different_tokens(self):
        """Testar que dois pedidos diferentes nunca recebem o mesmo token"""
        order2 = Order.objects.create(
            user=self.student,
            status='ready',
            payment_method='card',
            total_amount=Decimal('0.60'),
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time()
        )
        
        self.assertNotEqual(self.order.qr_token, order2.qr_token)
    
    def test_valid_token_finds_correct_order(self):
        """Testar que token válido encontra o pedido correto"""
        token = self.order.qr_token
        found_order = Order.objects.get(qr_token=token)
        self.assertEqual(found_order.pk, self.order.pk)
    
    def test_invalid_token_is_rejected(self):
        """Testar que token inválido é rejeitado"""
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': 'invalid_token_12345'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_student_cannot_use_staff_endpoint(self):
        """Testar que aluno não consegue utilizar endpoint de funcionário"""
        self.client.login(username='aluno_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        # Deve ser redirecionado ou negado (302 para login ou 403)
        self.assertIn(response.status_code, [302, 403])
    
    def test_teacher_cannot_use_staff_endpoint(self):
        """Testar que professor não consegue utilizar endpoint de funcionário"""
        self.client.login(username='professor_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_can_validate_token(self):
        """Testar que staff consegue validar token"""
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('order', data)
        self.assertEqual(data['order']['order_number'], self.order.order_number)
        self.assertEqual(data['order']['user_name'], self.student.get_full_name() or self.student.username)
        self.assertEqual(data['order']['turma'], '12PI')
    
    def test_admin_can_validate_token(self):
        """Testar que admin consegue validar token"""
        admin = User.objects.create_superuser(
            username='admin_qr', email='admin_qr@gmail.com', password='password123'
        )
        self.client.login(username='admin_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_picked_up_order_cannot_be_picked_up_again(self):
        """Testar que pedido já levantado não pode ser levantado novamente"""
        # Primeiro levantamento
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/confirm-pickup/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Tentar levantar novamente
        response = self.client.post(
            '/dashboard/confirm-pickup/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('já levantado', data['error'].lower())
    
    def test_cancelled_order_cannot_be_picked_up(self):
        """Testar que pedido cancelado não pode ser levantado"""
        cancelled_order = Order.objects.create(
            user=self.student,
            status='cancelled',
            payment_method='card',
            total_amount=Decimal('0.60'),
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time()
        )
        
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': cancelled_order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('cancelado', data['error'].lower())
    
    def test_pickup_confirmation_changes_status(self):
        """Testar que confirmação de levantamento altera corretamente o estado"""
        self.client.login(username='staff_qr', password='password123')
        
        self.assertEqual(self.order.status, 'ready')
        
        response = self.client.post(
            '/dashboard/confirm-pickup/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.picked_up_at)
        self.assertEqual(self.order.picked_up_by, self.staff)
    
    def test_concurrent_pickup_only_one_succeeds(self):
        """Testar duas confirmações concorrentes do mesmo pedido - apenas uma consegue"""
        self.client.login(username='staff_qr', password='password123')
        
        results = []
        errors = []
        
        def attempt_pickup():
            try:
                response = self.client.post(
                    '/dashboard/confirm-pickup/',
                    data=json.dumps({'token': self.order.qr_token}),
                    content_type='application/json'
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Criar duas threads para tentar levantar o mesmo pedido simultaneamente
        thread1 = threading.Thread(target=attempt_pickup)
        thread2 = threading.Thread(target=attempt_pickup)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Uma deve ter sucesso (200) e outra falhar (400)
        self.assertEqual(len(results), 2)
        self.assertIn(200, results)
        self.assertIn(400, results)
        
        # Verificar que o pedido foi levantado apenas uma vez
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
    
    def test_turma_displayed_correctly(self):
        """Testar que nome e turma corretos são apresentados"""
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['order']['turma'], '12PI')
        self.assertEqual(data['order']['user_name'], self.student.get_full_name() or self.student.username)
    
    def test_qr_does_not_contain_sensitive_data(self):
        """Testar que o QR não contém informação sensível desnecessária"""
        # O token deve ser apenas um identificador, não dados do pedido
        self.assertNotIn(self.order.order_number, self.order.qr_token)
        self.assertNotIn(self.student.username, self.order.qr_token)
        self.assertNotIn(str(self.order.total_amount), self.order.qr_token)
    
    def test_pickup_after_card_payment(self):
        """Testar que o fluxo continua a funcionar depois de uma encomenda paga por cartão escolar"""
        # Criar pedido pago por cartão
        card_order = Order.objects.create(
            user=self.student,
            status='ready',
            payment_method='card',
            total_amount=Decimal('1.20'),
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time()
        )
        OrderItem.objects.create(
            order=card_order,
            product=self.product,
            quantity=2,
            unit_price=Decimal('0.60'),
            subtotal=Decimal('1.20')
        )
        
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/validate-qr/',
            data=json.dumps({'token': card_order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_stock_balance_not_affected_by_pickup(self):
        """Testar que stock/saldo não é alterado novamente durante o levantamento"""
        initial_stock = self.product.stock
        initial_balance = self.student.balance
        
        self.client.login(username='staff_qr', password='password123')
        
        response = self.client.post(
            '/dashboard/confirm-pickup/',
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.product.refresh_from_db()
        self.student.refresh_from_db()
        
        # Stock e saldo não devem mudar durante pickup
        self.assertEqual(self.product.stock, initial_stock)
        self.assertEqual(self.student.balance, initial_balance)
