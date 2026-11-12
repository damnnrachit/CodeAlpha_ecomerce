from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem


class OrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='alice', password='Password123!')
        self.user_b = User.objects.create_user(username='bob', password='Password123!')

        self.category = Category.objects.create(name='Home', slug='home')
        self.product_blender = Product.objects.create(
            category=self.category,
            name='Kitchen Blender',
            slug='kitchen-blender',
            price=Decimal('50.00'),
            stock=10,
            is_active=True
        )
        self.product_toaster = Product.objects.create(
            category=self.category,
            name='Smart Toaster',
            slug='smart-toaster',
            price=Decimal('30.00'),
            stock=3,
            is_active=True
        )

        # Setup cart for user_a
        self.cart_a = Cart.objects.create(user=self.user_a)
        CartItem.objects.create(cart=self.cart_a, product=self.product_blender, quantity=2)
        CartItem.objects.create(cart=self.cart_a, product=self.product_toaster, quantity=1)

    def test_checkout_creates_order_and_reduces_stock(self):
        """Checkout atomically creates Order, OrderItems, decrements product stock, and clears cart."""
        self.client.login(username='alice', password='Password123!')
        checkout_url = reverse('orders:checkout')

        post_data = {
            'full_name': 'Alice Smith',
            'address': '456 Oak Avenue',
            'city': 'Metropolis',
            'postal_code': '12345',
        }

        response = self.client.post(checkout_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check Order was created
        order = Order.objects.filter(user=self.user_a).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'Alice Smith')
        self.assertEqual(order.status, Order.StatusChoices.PENDING)
        # Total: (2 * 50) + (1 * 30) = $130.00
        self.assertEqual(order.total, Decimal('130.00'))

        # Check OrderItems created
        self.assertEqual(order.items.count(), 2)

        # Check product stock decremented
        self.product_blender.refresh_from_db()
        self.product_toaster.refresh_from_db()
        self.assertEqual(self.product_blender.stock, 8)  # 10 - 2
        self.assertEqual(self.product_toaster.stock, 2)  # 3 - 1

        # Check user's cart is cleared
        self.assertEqual(self.cart_a.items.count(), 0)

    def test_checkout_rejects_insufficient_stock(self):
        """Checkout fails and rolls back if an item has insufficient stock."""
        # Manually lower stock of toaster to 0 before checkout
        self.product_toaster.stock = 0
        self.product_toaster.save()

        self.client.login(username='alice', password='Password123!')
        checkout_url = reverse('orders:checkout')

        post_data = {
            'full_name': 'Alice Smith',
            'address': '456 Oak Avenue',
            'city': 'Metropolis',
            'postal_code': '12345',
        }

        response = self.client.post(checkout_url, post_data)
        self.assertEqual(response.status_code, 200)

        # Verify NO order was created
        self.assertEqual(Order.objects.count(), 0)

        # Blender stock must NOT have changed (atomicity preserved)
        self.product_blender.refresh_from_db()
        self.assertEqual(self.product_blender.stock, 10)

        # Cart should NOT have been cleared
        self.assertEqual(self.cart_a.items.count(), 2)

    def test_simulate_payment(self):
        """Simulated payment marks an order as Paid."""
        order = Order.objects.create(
            user=self.user_a,
            full_name='Alice Smith',
            address='456 Oak Avenue',
            city='Metropolis',
            postal_code='12345',
            total=Decimal('100.00'),
            status=Order.StatusChoices.PENDING
        )

        self.client.login(username='alice', password='Password123!')
        pay_url = reverse('orders:simulate_payment', kwargs={'order_id': order.id})
        response = self.client.post(pay_url, follow=True)

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.StatusChoices.PAID)
        self.assertTrue(order.is_paid)

    def test_user_order_isolation(self):
        """Users can only view and access their own orders."""
        order_a = Order.objects.create(
            user=self.user_a,
            full_name='Alice Smith',
            address='456 Oak Avenue',
            city='Metropolis',
            postal_code='12345',
            total=Decimal('100.00'),
            status=Order.StatusChoices.PENDING
        )

        # Log in as Bob and try to access Alice's order receipt
        self.client.login(username='bob', password='Password123!')
        detail_url = reverse('orders:order_detail', kwargs={'order_id': order_a.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)  # 404 Not Found for Bob

        # Bob's order history should be empty
        history_url = reverse('orders:order_history')
        res_history = self.client.get(history_url)
        self.assertEqual(len(res_history.context['orders']), 0)
