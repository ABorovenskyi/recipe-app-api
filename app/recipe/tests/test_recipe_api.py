from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def create_recipe(user, **params):
    defaults = {
        'title': 'Some title',
        'time_in_minutes': 5,
        'price': Decimal('12.5'),
        'description': 'Some long description',
        'link': 'http://example.com/recipe/my-fovourite'
    }

    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email='email@example.com', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_retrive_recipes(self):
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        create_recipe(self.user)
        create_recipe(self.user)

        user2 = get_user_model().objects.create_user(email='user2@example.com', password='password123')
        create_recipe(user2)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)
