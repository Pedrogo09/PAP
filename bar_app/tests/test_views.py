from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from decimal import Decimal
from django.utils import timezone
from ..models import User, Product, Category, Order, OrderItem
import json
import threading


class UserFlowTests(TestCase):
    def test_register_and_login(self):
        # register a new user (gmail address) -> should be inactive until verification
        data = {
            'username': 'testuser',
            'email': 'testuser@gmail.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student',
            'password1': 'password123',
            'password2': 'password123',
        }
        resp = self.client.post(reverse('bar_app:register'), data)
        # registration now redirects to login because we require verification
        self.assertRedirects(resp, reverse('bar_app:login'))
        self.assertTrue(User.objects.filter(username='testuser').exists())
        u = User.objects.get(username='testuser')
        self.assertFalse(u.is_active)  # still inactive until clicked link

        # logout and try login (should be prevented)
        self.client.logout()
        login_resp = self.client.post(
            reverse('bar_app:login'),
            {'username': 'testuser', 'password': 'password123'},
            follow=True
        )
        from django.contrib.messages import get_messages
        messages = list(get_messages(login_resp.wsgi_request))
        self.assertTrue(any('Conta não activada' in str(m) for m in messages))
        self.assertFalse(login_resp.wsgi_request.user.is_authenticated)
    
    def test_register_requires_gmail(self):
        resp = self.client.post(reverse('bar_app:register'), {
            'username': 'u1',
            'email': 'notgmail@foo.com',
            'password1': 'p',
            'password2': 'p',
        })
        self.assertContains(resp, 'O email tem de ser uma conta Google')
        self.assertFalse(User.objects.filter(username='u1').exists())

    def test_email_verification_flow(self):
        # register with gmail address
        resp = self.client.post(reverse('bar_app:register'), {
            'username': 'u2',
            'email': 'u2@gmail.com',
            'password1': 'p',
            'password2': 'p',
        })
        # user created inactive
        u = User.objects.get(username='u2')
        self.assertFalse(u.is_active)
        self.assertFalse(u.email_verified)
        # email outbox should have one message
        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('activar a sua conta', mail.outbox[0].body)
        # extract token from body and verify
        import re
        match = re.search(r'/verify-email/([^\s/]+)', mail.outbox[0].body)
        self.assertIsNotNone(match)
        token = match.group(1)
        # call verification view
        vresp = self.client.get(reverse('bar_app:verify_email', args=[token]), follow=True)
        self.assertContains(vresp, 'Email verificado com sucesso')
        u.refresh_from_db()
        self.assertTrue(u.is_active)
        self.assertTrue(u.email_verified)


    def test_register_password_mismatch(self):
        data = {
            'username': 'x',
            'password1': 'a',
            'password2': 'b',
        }
        resp = self.client.post(reverse('bar_app:register'), data)
        self.assertContains(resp, 'As palavras-passe não coincidem.')
        self.assertFalse(User.objects.filter(username='x').exists())

    def test_login_invalid(self):
        resp = self.client.post(
            reverse('bar_app:login'),
            {'username': 'nope', 'password': 'nope'},
            follow=True
        )
        # built-in form will simply return to login page without authentication
        self.assertFalse(resp.wsgi_request.user.is_authenticated)


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p')
        self.category = Category.objects.create(name='Cat')
        self.product = Product.objects.create(
            name='Prod', price=1.0, stock=5, category=self.category
        )

    def test_add_to_cart_stock(self):
        # login first so we can inspect the cart page later
        self.client.login(username='u', password='p')
        self.client.get(reverse('bar_app:add_to_cart', args=[self.product.id]))
        # request cart page and assert product appears
        resp = self.client.get(reverse('bar_app:cart'))
        self.assertContains(resp, 'Prod')
        self.assertIn(str(self.product.price), resp.content.decode())

    def test_add_to_cart_no_stock(self):
        self.user = User.objects.create_user(username='u2', password='p2')
        self.client.login(username='u2', password='p2')
        self.product.stock = 0
        self.product.save()
        resp = self.client.get(reverse('bar_app:add_to_cart', args=[self.product.id]), follow=True)
        messages = list(resp.context.get('messages', []))
        self.assertTrue(any('Produto sem stock.' in str(m) for m in messages))
        # cart page should remain empty
        cart_resp = self.client.get(reverse('bar_app:cart'))
        self.assertNotContains(cart_resp, 'Prod')

    def test_cart_requires_login(self):
        # visit cart without login should redirect to login
        resp = self.client.get(reverse('bar_app:cart'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('bar_app:login'), resp.url)
        # after login, cart page should be accessible
        self.client.login(username='u', password='p')
        resp2 = self.client.get(reverse('bar_app:cart'))
        self.assertEqual(resp2.status_code, 200)


class ProductModelTests(TestCase):
    def test_stock_logic(self):
        p = Product(stock=1, min_stock=5)
        self.assertTrue(p.is_in_stock())
        self.assertTrue(p.needs_restock())
        p.stock = 0
        self.assertFalse(p.is_in_stock())


class PWATests(TestCase):
    def test_manifest_available(self):
        # static files are not served during tests, so read the file directly
        import os
        from django.conf import settings
        path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Bar Escolar', content)

    def test_service_worker_route(self):
        resp = self.client.get(reverse('bar_app:service_worker'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('self.addEventListener', resp.content.decode())


class EmailTests(TestCase):
    def setUp(self):
        # create a verified user with balance
        self.user = User.objects.create_user(
            username='emailuser',
            email='emailuser@gmail.com',
            password='p',
            first_name='E',
            last_name='U',
            is_active=True,
            email_verified=True
        )
        self.category = Category.objects.create(name='Cat')
        self.product = Product.objects.create(
            name='Prod', price=10, stock=10, category=self.category
        )
        # always allow scheduling any day
        from datetime import time, date
        from bar_app.models import WeekdayAvailability
        for wd in range(7):
            WeekdayAvailability.objects.create(weekday=wd, start_time=time(0,0), end_time=time(23,59), is_active=True)

    def test_topup_sends_email(self):
        from django.core import mail
        mail.outbox = []
        # create a fake transaction and generate pdf
        from bar_app.models import Transaction
        from bar_app.utils import generate_topup_pdf, send_pdf_email
        trans = Transaction.objects.create(
            user=self.user,
            transaction_type='topup',
            amount=15,
            description='teste'
        )
        pdf = generate_topup_pdf(trans)
        send_pdf_email(self.user, 'subj', 'body', pdf, 'file.pdf')
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].attachments)
        self.assertIn('subj', mail.outbox[0].subject)

    def test_order_sends_email(self):
        from django.core import mail
        mail.outbox = []
        from bar_app.models import Order, OrderItem, Transaction
        from bar_app.utils import generate_order_pdf, send_pdf_email
        # create order with one item
        order = Order.objects.create(
            user=self.user,
            payment_method='card',
            scheduled_date='2030-01-01',
            scheduled_time='10:00'
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, unit_price=self.product.price, subtotal=self.product.price)
        order.calculate_total()
        trans = Transaction.objects.create(
            user=self.user,
            transaction_type='payment',
            amount=order.total_amount,
            order=order,
            description='teste'
        )
        pdf = generate_order_pdf(order, trans)
        send_pdf_email(self.user, 'recibo', 'body', pdf, 'file.pdf')
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].attachments)
        self.assertIn('recibo', mail.outbox[0].subject)


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
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
            data=json.dumps({'token': 'invalid_token_12345'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_student_cannot_use_staff_endpoint(self):
        """Testar que aluno não consegue utilizar endpoint de funcionário"""
        self.client.force_login(self.student)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        # Deve ser redirecionado ou negado (302 para login ou 403)
        self.assertIn(response.status_code, [302, 403])
    
    def test_teacher_cannot_use_staff_endpoint(self):
        """Testar que professor não consegue utilizar endpoint de funcionário"""
        self.client.force_login(self.teacher)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_can_validate_token(self):
        """Testar que staff consegue validar token"""
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
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
        self.client.force_login(admin)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_picked_up_order_cannot_be_picked_up_again(self):
        """Testar que pedido já levantado não pode ser levantado novamente"""
        # Primeiro levantamento
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:confirm_pickup'),
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Tentar levantar novamente
        response = self.client.post(
            reverse('bar_app:confirm_pickup'),
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
        
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
            data=json.dumps({'token': cancelled_order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('cancelado', data['error'].lower())
    
    def test_pickup_confirmation_changes_status(self):
        """Testar que confirmação de levantamento altera corretamente o estado"""
        self.client.force_login(self.staff)
        
        self.assertEqual(self.order.status, 'ready')
        
        response = self.client.post(
            reverse('bar_app:confirm_pickup'),
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.picked_up_at)
        self.assertEqual(self.order.picked_up_by, self.staff)
    
    def test_turma_displayed_correctly(self):
        """Testar que nome e turma corretos são apresentados"""
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
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
        
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:validate_qr_token'),
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
        
        self.client.force_login(self.staff)
        
        response = self.client.post(
            reverse('bar_app:confirm_pickup'),
            data=json.dumps({'token': self.order.qr_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.product.refresh_from_db()
        self.student.refresh_from_db()
        
        # Stock e saldo não devem mudar durante pickup
        self.assertEqual(self.product.stock, initial_stock)
        self.assertEqual(self.student.balance, initial_balance)

