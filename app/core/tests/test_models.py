"""
Tetst for models
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Recipe


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'pass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normilized(self):
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@EXAMPLE.COM', 'test4@example.com'],
        ]

        for email, expected in sample_emails:
             user = get_user_model().objects.create_user(email=email, password='pass123')
             self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_an_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='pass123')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(email='test@example.com', password='pass123')

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user('test@example.com', 'password123')

        recipe = Recipe.objects.create(user=user, title='Sample recipe', time_in_minutes=5, price=Decimal('5.5'), description='bla bla bla')

        self.assertEqual(str(recipe), recipe.title)