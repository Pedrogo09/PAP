from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from ..models import User, Product, Category


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

