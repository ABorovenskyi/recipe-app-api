import tempfile, os

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from PIL import Image

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=(recipe_id,))

def image_upload_url(id):
    return reverse('recipe:recipe-upload-image', args=(id,))

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

def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='email@example.com', password='password123')
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

        user2 = create_user(email='user2@example.com', password='password123')
        create_recipe(user2)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)

        res = self.client.get(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = RecipeDetailSerializer(recipe).data
        self.assertEqual(res.data, data)

    def test_get_recipe_detail_resricted_by_user(self):
        user2 = create_user(email='example@example.com', password='asdsadasd', name='john doe')

        recipe = create_recipe(user=user2)

        res = self.client.get(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recipe(self):
        payload = {'title': 'recipe title', 'time_in_minutes': 30, 'price':Decimal('5.99')}
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        title = 'recipe title'
        link = 'http://google.com'
        recipe = create_recipe(self.user, title=title)

        res = self.client.patch(detail_url(recipe.id), {'link': link})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.link, link)
        self.assertEqual(recipe.title, title)

    def test_full_update(self):
        recipe = create_recipe(self.user)

        payload = {'title':'NEW', 'link': 'http://new.new', 'price': Decimal('1.0'), 'time_in_minutes': 300}

        res = self.client.put(detail_url(recipe.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

    def test_can_not_update_user(self):
        user2 = create_user(email='user2@example.com', password='1sfrgunu49nin')
        recipe = create_recipe(self.user)

        res = self.client.patch(detail_url(recipe.id), {'user': user2})
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(self.user)

        res = self.client.delete(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        user2 = create_user(email='user2@example.com', password='1sfrgunu49nin')
        recipe = create_recipe(user2)

        res = self.client.delete(detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {'title': 'recipe title', 'time_in_minutes': 30, 'price':Decimal('5.99'), 'tags': [{'name': 'tag1'}, {'name': 'tag2'}]}
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(title=payload['title'])

        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(name=tag['name'], user=self.user).exists())

    def test_create_recipe_with_existing_tags(self):
        tag = Tag.objects.create(name='tag123', user=self.user)
        payload = {'title': 'recipe title', 'time_in_minutes': 30, 'price':Decimal('5.99'), 'tags': [{'name': tag.name}, {'name': 'tag222'}]}
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(title=payload['title'])

        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(name=tag['name'], user=self.user).exists())

    def test_update_recipe_tags(self):
        recipe = create_recipe(self.user)
        payload = {'tags': [{'name': 'tag1'}]}

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag = Tag.objects.get(name=payload['tags'][0]['name'], user=self.user)

        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_existing_tag(self):
        tag = Tag.objects.create(name='tag34', user=self.user)
        recipe = create_recipe(self.user)
        recipe.tags.add(tag)

        tag2 = Tag.objects.create(name='tag56', user=self.user)

        payload = {'tags': [{'name': tag.name}, {'name': tag2.name}]}
        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(tag, recipe.tags.all())
        self.assertIn(tag2, recipe.tags.all())

    def test_clearing_recipe_tags(self):
        tag = Tag.objects.create(name='tag34', user=self.user)
        recipe = create_recipe(self.user)
        recipe.tags.add(tag)

        res = self.client.patch(detail_url(recipe.id), {'tags': []}, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        payload = {'title': 'recipe title', 'time_in_minutes': 30, 'price':Decimal('5.99'), 'ingredients': [{'name': 'ing1'}, {'name': 'ing2'}]}

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for obj in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(name=obj['name']).exists())

    def test_create_recipe_with_existing_ingredients(self):
        ing = Ingredient.objects.create(user=self.user, name='ingr123')
        payload = {'title': 'recipe title', 'time_in_minutes': 30, 'price':Decimal('5.99'), 'ingredients': [{'name': 'ing1'}, {'name': ing.name}]}

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(Ingredient.objects.filter(user=self.user).count(), 2)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)

        for obj in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(name=obj['name']).exists())

    def test_update_recipe_with_new_ingredients(self):
        recipe = create_recipe(self.user)
        payload = {'ingredients': [{'name': 'ing1'}, {'name': 'ing2'}]}

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 2)

        for obj in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(name=obj['name']).exists())

    def test_update_recipe_with_existing_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name='ing99')
        recipe = create_recipe(self.user)
        payload = {'ingredients': [{'name': ingredient.name}, {'name': 'ing2'}]}

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 2)

        ingredient2 = Ingredient.objects.get(user=self.user, name=payload['ingredients'][1]['name'])

        self.assertIn(ingredient, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_remove_ingredients_from_recipe(self):
        recipe = create_recipe(self.user)
        recipe.ingredients.add(Ingredient.objects.create(user=self.user, name='ing99'))
        recipe.ingredients.add(Ingredient.objects.create(user=self.user, name='ing00'))

        res = self.client.patch(detail_url(recipe.id), {'ingredients': []}, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='email@example.com', password='password123')
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)

            res = self.client.post(url, {'image': image_file}, format='multipart')

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)

        payload = {'image': 'some string'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)