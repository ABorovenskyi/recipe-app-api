from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGRIDIENT_URL = reverse('recipe:ingredient-list')

def detail_url(id):
    return reverse('recipe:ingredient-detail', args=(id,))

def create_user(email='user@exmaple.com', password='pasdfgqeg'):
    return get_user_model().objects.create_user(email=email, password=password)

def create_ingredient(user, name):
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGRIDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_get_ingridients_list(self):
        ingredients = [create_ingredient(self.user, 'ing 1'), create_ingredient(self.user, 'ing 2')]

        res = self.client.get(INGRIDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = IngredientSerializer(reversed(ingredients), many=True).data

        self.assertEqual(res.data, data)

    def test_ingredients_limited_by_user(self):
        ingredients = [create_ingredient(self.user, 'ing 1'), create_ingredient(self.user, 'ing 2')]

        user2 = create_user('user2@example.com')
        create_ingredient(user2, 'ing 3')

        res = self.client.get(INGRIDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = IngredientSerializer(reversed(ingredients), many=True).data

        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, data)

    def test_update_ingridient(self):
        ing = create_ingredient(self.user, 'ing1')

        payload = {'name': 'new name'}
        res = self.client.patch(detail_url(ing.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ing.refresh_from_db()

        self.assertEqual(ing.name, payload['name'])

    def test_delete_ingridient(self):
        ing = create_ingredient(self.user, 'ing1')

        res = self.client.delete(detail_url(ing.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ing.id).exists())
