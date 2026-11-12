from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Category, Product
from .models import Cart, CartItem


class CartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cartuser',
            password='Password123!'
        )
        self.category = Category.objects.create(name='Gadgets', slug='gadgets')
        self.product = Product.objects.create(
            category=self.category,
            name='Smart Watch',
            slug='smart-watch',
            price=Decimal('150.00'),
            stock=5,
            is_active=True
        )

    def test_cart_requires_login(self):
        """Unauthenticated access redirects to login."""
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_add_to_cart_standard_post(self):
        """Authenticated user can add a product to cart via standard POST."""
        self.client.login(username='cartuser', password='Password123!')
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.product.id})
        response = self.client.post(url, {'quantity': 2}, follow=True)

        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.get_total_items(), 2)
        self.assertEqual(cart.get_total_price(), Decimal('300.00'))

    def test_add_to_cart_ajax(self):
        """AJAX request returns JSON with updated count and price."""
        self.client.login(username='cartuser', password='Password123!')
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.product.id})
        response = self.client.post(
            url,
            {'quantity': 1},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_item_count'], 1)
        self.assertEqual(data['cart_total_price'], '150.00')

    def test_add_to_cart_exceeding_stock(self):
        """Adding quantity beyond available stock caps at available stock."""
        self.client.login(username='cartuser', password='Password123!')
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.product.id})
        self.client.post(url, {'quantity': 10}, follow=True)

        cart_item = CartItem.objects.get(cart__user=self.user, product=self.product)
        self.assertEqual(cart_item.quantity, 5)  # capped at stock (5)

    def test_update_cart_quantity_increase_and_decrease(self):
        """Updating quantity increases and decreases correctly."""
        self.client.login(username='cartuser', password='Password123!')
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        update_url = reverse('cart:update_cart_item', kwargs={'item_id': item.id})

        # Increase via AJAX
        res_inc = self.client.post(
            update_url,
            {'action': 'increase'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(res_inc.status_code, 200)
        data_inc = res_inc.json()
        self.assertEqual(data_inc['quantity'], 3)
        self.assertEqual(data_inc['cart_total'], '450.00')

        # Decrease via AJAX
        res_dec = self.client.post(
            update_url,
            {'action': 'decrease'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(res_dec.status_code, 200)
        data_dec = res_dec.json()
        self.assertEqual(data_dec['quantity'], 2)

    def test_decrease_to_zero_removes_item(self):
        """Decreasing quantity of 1 deletes the cart item."""
        self.client.login(username='cartuser', password='Password123!')
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        update_url = reverse('cart:update_cart_item', kwargs={'item_id': item.id})
        res = self.client.post(
            update_url,
            {'action': 'decrease'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['removed'])
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_remove_cart_item(self):
        """Directly removing an item deletes it and recalculates totals."""
        self.client.login(username='cartuser', password='Password123!')
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        remove_url = reverse('cart:remove_cart_item', kwargs={'item_id': item.id})
        res = self.client.post(
            remove_url,
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['removed'])
        self.assertEqual(data['cart_item_count'], 0)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())
