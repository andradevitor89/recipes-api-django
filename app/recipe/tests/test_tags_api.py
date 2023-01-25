from core.models import Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient

TAGS_URL = reverse('recipe:tag-list')
TAG_MOCK_OBJECT = {'name': 'Sauce'}


def create_user(email='sample@example.com', password='passtest123'):
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def create_tag(user, **params):
    defaults = TAG_MOCK_OBJECT
    defaults.update(params)
    recipe = Tag.objects.create(user=user, **defaults)
    return recipe


class PublicTagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        create_tag(self.user, name='Vegan')
        create_tag(self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_list_limited_to_user(self):
        tag = create_tag(self.user)

        other_user = create_user(
            email='newuser@example.com',
            password='testpass123'
        )

        create_tag(other_user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    # def test_get_recipe_detail(self):
    #     recipe = create_tag(self.user)
    #     url = detail_url(recipe.id)

    #     res = self.client.get(url)

    #     serializer = RecipeDetailSerializer(recipe)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertEqual(res.data, serializer.data)

#     def test_create_recipe(self):
#         res = self.client.post(TAGS_URL, TAG_MOCK_OBJECT)

#         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
#         recipe = Recipe.objects.get(id=res.data['id'])

#         for key, value in TAG_MOCK_OBJECT.items():
#             self.assertEqual(getattr(recipe, key), value)

#         self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        tag = create_tag(user=self.user)
        payload = {
            'name': 'Patched name'
        }
        url = detail_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)

#     def test_full_update(self):
#         recipe = create_tag(user=self.user)
#         payload = {'title': 'Patched title',
#                    'description': 'Patched description',
#                    'price': Decimal('15.5'),
#                    'time_minutes': 54,
#                    'link': 'http://exammple.com/patched-recipe.pdf'}
#         url = detail_url(recipe.id)

#         res = self.client.put(url, payload)

#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         recipe.refresh_from_db()
#         for key, value in payload.items():
#             self.assertEqual(getattr(recipe, key), value)

#         self.assertEqual(recipe.user, self.user)

#     def test_update_user_returns_error(self):
#         recipe = create_tag(user=self.user)
#         other_user = create_user(
#             email='otheruser@example.com',
#             password='passtest1234'
#         )
#         payload = {'user': other_user.id}

#         url = detail_url(recipe.id)

#         res = self.client.patch(url, payload)
#         recipe.refresh_from_db()
#         self.assertEqual(recipe.user, self.user)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)

#     def test_delete(self):
#         recipe = create_tag(user=self.user)

#         url = detail_url(recipe.id)

#         res = self.client.delete(url)
#         self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

#     def test_delete_other_user_recipe(self):
#         other_user = create_user(
#             email='otheruser@example.com',
#             password='passtest1234'
#         )
#         recipe = create_tag(user=other_user)
#         url = detail_url(recipe.id)

#         res = self.client.delete(url)
#         self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
