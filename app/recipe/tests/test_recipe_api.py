from decimal import Decimal

from core.models import Recipe, Tag
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


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        create_recipe(self.user)

        other_user = create_user(
            email='newuser@example.com',
            password='testpass123'
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

    def test_partial_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Patched title'
        }
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.description, RECIPE_MOCK_OBJECT['description'])
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.price, RECIPE_MOCK_OBJECT['price'])
        self.assertEqual(recipe.time_minutes,
                         RECIPE_MOCK_OBJECT['time_minutes'])
        self.assertEqual(recipe.link, RECIPE_MOCK_OBJECT['link'])
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(user=self.user)
        payload = {'title': 'Patched title',
                   'description': 'Patched description',
                   'price': Decimal('15.5'),
                   'time_minutes': 54,
                   'link': 'http://exammple.com/patched-recipe.pdf'}
        url = detail_url(recipe.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        recipe = create_recipe(user=self.user)
        other_user = create_user(
            email='otheruser@example.com',
            password='passtest1234'
        )
        payload = {'user': other_user.id}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe(self):
        other_user = create_user(
            email='otheruser@example.com',
            password='passtest1234'
        )
        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_with_new_tags(self):
        payload = {'title': 'Sample recipe title',
                   'description': 'Sample recipe description',
                   'price': Decimal('10.5'),
                   'time_minutes': 10,
                   'link': 'http://exammple.com/recipe.pdf',
                   'tags': [{
                       'name': 'Dinner'
                   }, {
                       'name': 'Thai'
                   }]}

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                name=tag['name'], user=self.user).exists())

    def test_create_with_existing_tags(self):
        indian_tag = Tag.objects.create(user=self.user, name='Indian')
        # try reusing the base payload
        payload = {'title': 'Sample recipe title',
                   'description': 'Sample recipe description',
                   'price': Decimal('10.5'),
                   'time_minutes': 10,
                   'link': 'http://exammple.com/recipe.pdf',
                   'tags': [{
                       'name': 'Indian'
                   }, {
                       'name': 'Thai'
                   }]}
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(indian_tag, recipe.tags.all())
        #  assert there is only 2 tags in db
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                name=tag['name'], user=self.user).exists())
