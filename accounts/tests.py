from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, InviteToken


class AccountsTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123'
        )

    def test_create_and_use_invite_token(self):
        token = InviteToken.create_for_user(self.admin, days=3)
        self.assertTrue(token.is_valid())
        self.assertFalse(token.is_used)

        # Register new user with this token
        response = self.client.post(f'/accounts/register/{token.token}/', {
            'username': 'shopper',
            'first_name': 'Test',
            'last_name': 'Shopper',
            'email': 'shopper@test.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 302)

        # Check token is consumed
        token.refresh_from_db()
        self.assertTrue(token.is_used)
        self.assertFalse(token.is_valid())
        self.assertIsNotNone(token.used_by)
        self.assertEqual(token.used_by.username, 'shopper')
