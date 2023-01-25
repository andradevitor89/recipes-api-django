
from django.contrib.auth import get_user_model
from django.test import TestCase
from decimal import Decimal
from core import models


def create_user(email='sample@example.com', password='passtest123'):
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        user = get_user_model().objects.create_user(
            'Name3@EMAil.COM',
            'sample123')
        self.assertEqual(user.email, 'Name3@email.com')

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'sample123')

    def test_create_super_user(self):
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            'Name3@EMAil.COM',
            'sample123')
        recipe = models.Recipe.objects.create(
            user=user,
            title='Carbonara',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sauce for pasta'
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = create_user()
        tag = models.Tag.objects.create(
            name='Sauce',
            user=user
        )
        self.assertEqual(str(tag), tag.name)
