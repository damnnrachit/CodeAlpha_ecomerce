import os
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from store.models import Category, Product
from cart.models import Cart


class Command(BaseCommand):
    help = 'Seeds sample categories, products with realistic placeholder images, and demo accounts.'

    def _create_placeholder_image(self, title: str, category_name: str, bg_color: tuple, text_color: tuple) -> bytes:
        """
        Generates a clean 600x600 PNG banner using Pillow for product catalog display.
        """
        width, height = 600, 600
        image = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(image)

        # Draw stylish decorative top bar
        draw.rectangle([(0, 0), (width, 16)], fill=(79, 70, 229))

        # Draw decorative inner frame
        margin = 30
        draw.rounded_rectangle(
            [(margin, margin), (width - margin, height - margin)],
            radius=20,
            outline=(226, 232, 240),
            width=3
        )

        # Draw category pill tag
        tag_text = f"  {category_name.upper()}  "
        draw.text((60, 60), tag_text, fill=(79, 70, 229))

        # Center product label text
        words = title.split()
        lines = []
        cur_line = []
        for word in words:
            if len(' '.join(cur_line + [word])) < 22:
                cur_line.append(word)
            else:
                lines.append(' '.join(cur_line))
                cur_line = [word]
        if cur_line:
            lines.append(' '.join(cur_line))

        y_offset = 240
        for line in lines:
            draw.text((60, y_offset), line, fill=text_color)
            y_offset += 32

        # Draw footer logo
        draw.text((60, 520), "SwiftShop Verified Product", fill=(148, 163, 184))

        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("--- Starting SwiftShop Database Seeding ---"))

        # 1. Categories definition
        categories_data = [
            {
                'name': 'Electronics',
                'slug': 'electronics',
                'description': 'Cutting-edge gadgets, audio gear, computing accessories, and smart devices.',
                'bg_color': (241, 245, 249),
                'text_color': (15, 23, 42),
            },
            {
                'name': 'Fashion & Apparel',
                'slug': 'fashion-apparel',
                'description': 'Contemporary, durable apparel and accessories designed for daily comfort.',
                'bg_color': (248, 250, 252),
                'text_color': (30, 41, 59),
            },
            {
                'name': 'Home & Kitchen',
                'slug': 'home-kitchen',
                'description': 'High-performance culinary tools, modern home decor, and living essentials.',
                'bg_color': (254, 252, 232),
                'text_color': (69, 26, 3),
            },
        ]

        created_categories = {}
        for cat_info in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_info['slug'],
                defaults={
                    'name': cat_info['name'],
                    'description': cat_info['description'],
                }
            )
            created_categories[cat.slug] = (cat, cat_info)
            status_str = "Created" if created else "Existing"
            self.stdout.write(f"  [Category] {status_str}: {cat.name}")

        # 2. Products dataset (15 realistic items across the 3 categories)
        products_data = [
            # Electronics (5)
            {
                'category_slug': 'electronics',
                'name': 'UltraHD Noise-Cancelling Headphones',
                'slug': 'ultrahd-noise-cancelling-headphones',
                'description': 'Industry-leading active noise cancellation with 40mm neodymium dynamic drivers, 36-hour playback battery life, and crystal-clear beamforming microphone for meetings.',
                'price': Decimal('199.99'),
                'stock': 24,
            },
            {
                'category_slug': 'electronics',
                'name': 'Mechanical RGB Gaming Keyboard',
                'slug': 'mechanical-rgb-gaming-keyboard',
                'description': 'Tactile mechanical switches with per-key RGB backlighting, durable aluminum frame, braided USB-C cable, and onboard memory profiles.',
                'price': Decimal('89.99'),
                'stock': 18,
            },
            {
                'category_slug': 'electronics',
                'name': '4K Curved Ultrawide Monitor 34-Inch',
                'slug': '4k-curved-ultrawide-monitor-34-inch',
                'description': 'Immersive 1500R curvature with 144Hz refresh rate, 1ms response time, HDR400 color precision, and versatile USB hub connectivity.',
                'price': Decimal('449.99'),
                'stock': 8,
            },
            {
                'category_slug': 'electronics',
                'name': 'Portable Bluetooth Waterproof Speaker',
                'slug': 'portable-bluetooth-waterproof-speaker',
                'description': 'IPX7 fully submersible waterproof body with 360-degree room-filling acoustic sound, deep punchy bass, and 20 hours continuous playtime.',
                'price': Decimal('49.99'),
                'stock': 35,
            },
            {
                'category_slug': 'electronics',
                'name': 'Ergonomic Wireless Vertical Mouse',
                'slug': 'ergonomic-wireless-vertical-mouse',
                'description': 'Natural 57-degree handshake grip position to minimize wrist strain and carpal fatigue. Dual Bluetooth and 2.4G wireless pairing.',
                'price': Decimal('39.99'),
                'stock': 40,
            },

            # Fashion & Apparel (5)
            {
                'category_slug': 'fashion-apparel',
                'name': 'Vintage Classic Denim Jacket',
                'slug': 'vintage-classic-denim-jacket',
                'description': 'Authentic 100% heavyweight cotton denim crafted with vintage brass hardware, button-flap chest pockets, and relaxed tailored silhouette.',
                'price': Decimal('79.99'),
                'stock': 22,
            },
            {
                'category_slug': 'fashion-apparel',
                'name': 'Organic Cotton Crewneck T-Shirt',
                'slug': 'organic-cotton-crewneck-tshirt',
                'description': 'Ultra-soft combed organic cotton jersey t-shirt with reinforced ribbed collar, preshrunk fit, and eco-certified non-toxic dyes.',
                'price': Decimal('24.99'),
                'stock': 65,
            },
            {
                'category_slug': 'fashion-apparel',
                'name': 'Urban Water-Resistant Everyday Backpack',
                'slug': 'urban-water-resistant-everyday-backpack',
                'description': 'Durable ballistic nylon backpack with padded 16-inch laptop compartment, hidden anti-theft rear pocket, and breathable airflow back panel.',
                'price': Decimal('59.99'),
                'stock': 28,
            },
            {
                'category_slug': 'fashion-apparel',
                'name': 'All-Weather Lightweight Windbreaker',
                'slug': 'all-weather-lightweight-windbreaker',
                'description': 'Breathable water-repellent shell with adjustable drawstring hood, zippered storm pockets, and packable stowaway pouch.',
                'price': Decimal('89.99'),
                'stock': 16,
            },
            {
                'category_slug': 'fashion-apparel',
                'name': 'Polarized UV400 Classic Aviator Sunglasses',
                'slug': 'polarized-uv400-classic-aviator-sunglasses',
                'description': 'Sleek metal alloy frame with shatterproof polarized polycarbonate lenses delivering 100% UVA/UVB protection and glare elimination.',
                'price': Decimal('34.99'),
                'stock': 45,
            },

            # Home & Kitchen (5)
            {
                'category_slug': 'home-kitchen',
                'name': 'Stainless Steel Programmable Coffee Maker',
                'slug': 'stainless-steel-programmable-coffee-maker',
                'description': '12-cup precision thermal brewing system with 24-hour auto-brew programming, custom brew-strength selector, and anti-drip carafe.',
                'price': Decimal('69.99'),
                'stock': 19,
            },
            {
                'category_slug': 'home-kitchen',
                'name': 'Cast Iron Pre-Seasoned Dutch Oven 5-Qt',
                'slug': 'cast-iron-pre-seasoned-dutch-oven-5qt',
                'description': 'Heavy-duty enameled cast iron delivering superior heat distribution and moisture retention for artisan sourdough baking, stews, and braises.',
                'price': Decimal('54.99'),
                'stock': 14,
            },
            {
                'category_slug': 'home-kitchen',
                'name': 'Smart True-HEPA Air Purifier',
                'slug': 'smart-true-hepa-air-purifier',
                'description': 'Three-stage filtration system capturing 99.97% of airborne pollen, pet dander, and odors in rooms up to 500 sq ft with whisper-quiet sleep mode.',
                'price': Decimal('129.99'),
                'stock': 12,
            },
            {
                'category_slug': 'home-kitchen',
                'name': 'Ceramic Non-Stick Cookware 10-Piece Set',
                'slug': 'ceramic-non-stick-cookware-10-piece-set',
                'description': 'Toxin-free healthy ceramic non-stick cooking surface (PTFE/PFOA free) with induction-ready aluminum bases and stay-cool silicone handles.',
                'price': Decimal('119.99'),
                'stock': 10,
            },
            {
                'category_slug': 'home-kitchen',
                'name': 'Minimalist LED Dimmable Desk Lamp',
                'slug': 'minimalist-led-dimmable-desk-lamp',
                'description': 'Flicker-free eye-care LED lamp with 5 color temperature settings, smooth touch dimming slider, and integrated USB fast-charging port.',
                'price': Decimal('29.99'),
                'stock': 50,
            },
        ]

        os.makedirs(settings.MEDIA_ROOT / 'products', exist_ok=True)

        for p_info in products_data:
            cat, cat_meta = created_categories[p_info['category_slug']]
            product, created = Product.objects.get_or_create(
                slug=p_info['slug'],
                defaults={
                    'category': cat,
                    'name': p_info['name'],
                    'description': p_info['description'],
                    'price': p_info['price'],
                    'stock': p_info['stock'],
                    'is_active': True,
                }
            )

            # Generate and attach placeholder image if missing
            if not product.image:
                img_bytes = self._create_placeholder_image(
                    title=product.name,
                    category_name=cat.name,
                    bg_color=cat_meta['bg_color'],
                    text_color=cat_meta['text_color'],
                )
                filename = f"{product.slug}.png"
                product.image.save(filename, ContentFile(img_bytes), save=True)

            status_str = "Created" if created else "Existing"
            self.stdout.write(f"  [Product] {status_str}: {product.name} (${product.price}, Stock: {product.stock})")

        # 3. Create demo users
        # Superuser: admin / admin123
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@swiftshop.local',
                password='admin123'
            )
            Cart.objects.get_or_create(user=admin_user)
            self.stdout.write(self.style.SUCCESS("  [User] Superuser created: admin / admin123"))
        else:
            self.stdout.write("  [User] Superuser 'admin' already exists.")

        # Customer: customer / customer123
        if not User.objects.filter(username='customer').exists():
            demo_customer = User.objects.create_user(
                username='customer',
                email='customer@swiftshop.local',
                password='customer123',
                first_name='Demo',
                last_name='Customer'
            )
            Cart.objects.get_or_create(user=demo_customer)
            self.stdout.write(self.style.SUCCESS("  [User] Demo customer created: customer / customer123"))
        else:
            self.stdout.write("  [User] Demo customer 'customer' already exists.")

        self.stdout.write(self.style.SUCCESS("\n--- Database Seeding Completed Successfully! ---"))
        self.stdout.write(self.style.SUCCESS(f"Total Categories: {Category.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Total Products:   {Product.objects.count()}"))
