from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, Product


class StoreViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category_tech = Category.objects.create(name='Electronics', slug='electronics')
        self.category_fashion = Category.objects.create(name='Fashion', slug='fashion')

        # Create 10 products in Electronics to test 8-per-page pagination
        self.products = []
        for i in range(1, 11):
            p = Product.objects.create(
                category=self.category_tech,
                name=f"Tech Gadget {i:02d}",
                slug=f"tech-gadget-{i:02d}",
                description=f"Advanced electronics device #{i}",
                price=Decimal(f"{i * 10}.99"),
                stock=i * 5,
                is_active=True
            )
            self.products.append(p)

        # Create 2 fashion items
        self.fashion_item = Product.objects.create(
            category=self.category_fashion,
            name="Classic Denim Jacket",
            slug="classic-denim-jacket",
            description="Timeless blue denim outerwear",
            price=Decimal("79.99"),
            stock=12,
            is_active=True
        )

        # Inactive product
        self.inactive_product = Product.objects.create(
            category=self.category_tech,
            name="Archived Prototype",
            slug="archived-prototype",
            price=Decimal("199.99"),
            stock=0,
            is_active=False
        )

    def test_product_list_status_and_pagination(self):
        """Catalog page loads and respects 8-items-per-page limit."""
        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(response.status_code, 200)

        # Total active products: 10 tech + 1 fashion = 11 products
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 8)  # Exactly 8 on page 1
        self.assertTrue(page_obj.has_next())

        # Page 2 should have the remaining 3 items
        response_p2 = self.client.get(reverse('store:product_list') + '?page=2')
        self.assertEqual(response_p2.status_code, 200)
        self.assertEqual(len(response_p2.context['page_obj']), 3)

    def test_product_list_category_filter(self):
        """Filtering by category returns only products in that category."""
        response = self.client.get(reverse('store:product_list') + '?category=fashion')
        self.assertEqual(response.status_code, 200)
        products = response.context['page_obj'].object_list
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Classic Denim Jacket")

    def test_product_list_search(self):
        """Search query filters products by name or description."""
        response = self.client.get(reverse('store:product_list') + '?q=Denim')
        self.assertEqual(response.status_code, 200)
        products = response.context['page_obj'].object_list
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].slug, "classic-denim-jacket")

    def test_product_detail_view(self):
        """Product detail renders active product details."""
        url = reverse('store:product_detail', kwargs={'slug': 'classic-denim-jacket'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.fashion_item)
        self.assertContains(response, "Classic Denim Jacket")
        self.assertContains(response, "$79.99")

    def test_inactive_product_detail_returns_404(self):
        """Inactive product detail page returns 404."""
        url = reverse('store:product_detail', kwargs={'slug': 'archived-prototype'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
