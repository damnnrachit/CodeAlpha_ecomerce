from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from cart.models import Cart


class AccountAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='Password123!'
        )

    def test_registration_success(self):
        """Valid registration creates a user, creates a cart, and logs them in."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check user created in database
        user = User.objects.filter(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')

        # Check cart auto-created
        self.assertTrue(Cart.objects.filter(user=user).exists())

        # Check session is authenticated
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_duplicate_username(self):
        """Registration with existing username returns validation error."""
        data = {
            'username': 'existinguser',
            'email': 'unique@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors.get('username'))
        self.assertIn('A user with that username already exists.', form.errors['username'])

    def test_registration_duplicate_email(self):
        """Registration with existing email returns validation error."""
        data = {
            'username': 'uniqueuser',
            'email': 'existing@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors.get('email'))
        self.assertIn('A user with that email already exists.', form.errors['email'])

    def test_registration_password_mismatch(self):
        """Registration with non-matching passwords returns validation error."""
        data = {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'DifferentPassword456!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors.get('confirm_password'))
        self.assertIn('Passwords do not match.', form.errors['confirm_password'])

    def test_login_success(self):
        """Valid login authenticates user and sets session."""
        response = self.client.post(self.login_url, {
            'username': 'existinguser',
            'password': 'Password123!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_invalid_credentials(self):
        """Invalid password fails authentication."""
        response = self.client.post(self.login_url, {
            'username': 'existinguser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout(self):
        """Logout flushes session."""
        self.client.login(username='existinguser', password='Password123!')
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
