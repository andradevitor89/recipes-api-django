from core.models import Ingredient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse('recipe:ingredient-list')
INGREDIENT_MOCK_OBJECT = {'name': 'Parmesan'}


def create_user(email='sample@example.com', password='passtest123'):
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(tag_id):
    return reverse('recipe:ingredient-detail', args=[tag_id])


def create_ingredient(user, **params):
    defaults = INGREDIENT_MOCK_OBJECT
    defaults.update(params)
    recipe = Ingredient.objects.create(user=user, **defaults)
    return recipe


class PublicTagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        create_ingredient(self.user, name='Cheese')
        create_ingredient(self.user, name='Flour')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_list_limited_to_user(self):
        ingredient = create_ingredient(self.user, name='Cheese')

        other_user = create_user(
            email='newuser@example.com'
        )

        create_ingredient(other_user, name='Flour')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)
