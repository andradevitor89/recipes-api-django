from decimal import Decimal

from core.models import Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse('recipe:recipe-list')
RECIPE_MOCK_OBJECT = {'title': 'Sample recipe title',
                      'description': 'Sample recipe description',
                      'price': Decimal('10.5'),
                      'time_minutes': 10,
                      'link': 'http://exammple.com/recipe.pdf'}


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    defaults = RECIPE_MOCK_OBJECT
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        # self.assertEqual(len(recipes), 2)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        create_recipe(self.user)

        other_user = get_user_model().objects.create_user(
            'newuser@example.com',
            'testpass123'
        )

        create_recipe(other_user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        res = self.client.post(RECIPES_URL, RECIPE_MOCK_OBJECT)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in RECIPE_MOCK_OBJECT.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)
