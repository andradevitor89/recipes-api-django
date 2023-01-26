from decimal import Decimal

from core.models import Recipe, Tag, Ingredient
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


def create_tag(user, **params):
    defaults = {
        'name': 'Indian'
    }
    defaults.update(params)

    return Tag.objects.create(user=user, **defaults)


def create_ingredient(user, **params):
    defaults = {
        'name': 'Salt'
    }
    defaults.update(params)

    return Ingredient.objects.create(user=user, **defaults)


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

    def test_create_tag_when_updating_recipe(self):
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{
            'name': 'Indian'
        }]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag = Tag.objects.get(user=self.user, name='Indian')
        self.assertIsNotNone(tag)
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        indian_tag = Tag.objects.create(user=self.user, name='Indian')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(indian_tag)
        lunch_tag = Tag.objects.create(user=self.user, name='Lunch')

        payload = {'tags': [{
            'name': 'Lunch'
        }]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(lunch_tag, recipe.tags.all())
        self.assertNotIn(indian_tag, recipe.tags.all())

    def test_clear_recipes_tags(self):
        recipe = create_recipe(user=self.user)
        tag = create_tag(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # self.assertEqual(recipe.tags.all().count(), 0)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_ingredients_when_create_recipe(self):

        payload = RECIPE_MOCK_OBJECT.copy()
        payload.update({
            'ingredients': [
                {
                    'name': 'Salt'
                }
            ]
        })

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 1)

        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                name=ingredient['name'], user=self.user).exists())

    def test_create_recipe_with_existing_ingredient(self):

        ingredient1 = create_ingredient(self.user, **{'name': 'Lemon'})
        ingredient2 = create_ingredient(self.user, **{'name': 'Tomato'})
        payload = RECIPE_MOCK_OBJECT.copy()
        payload.update({
            'ingredients': [
                {
                    'name': ingredient1.name
                },
                {
                    'name': ingredient2.name
                },
            ]
        })

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertTrue(recipe.ingredients.count(), 2)
        self.assertIn(ingredient1, recipe.ingredients.all())

        for payload_ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                name=payload_ingredient['name'], user=self.user).exists())

        self.assertEqual(Ingredient.objects.all().count(), 2)

    def test_create_ingredient_when_update_recipe(self):

        recipe = create_recipe(self.user)

        payload = {
            'ingredients': [
                {
                    'name': 'Lettuce'
                }
            ]
        }
        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(ingredients.count(), 1)
        ingredient = ingredients[0]
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_assign_existing_ingredient_when_update_recipe(self):

        ingredient_pepper = create_ingredient(self.user, name='Pepper')
        ingredient_chili = create_ingredient(self.user, name='Chili')
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient_pepper)

        payload = {
            'ingredients': [
                {
                    'name': ingredient_chili.name
                }
            ]
        }

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_chili, recipe.ingredients.all())
        self.assertNotIn(ingredient_pepper, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient_pepper = create_ingredient(self.user, name='Pepper')
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient_pepper)

        payload = {
            'ingredients': []
        }

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
