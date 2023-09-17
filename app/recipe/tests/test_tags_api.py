from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=(tag_id,))

def create_user(email='user@example.com', password='qwerty'):
    return get_user_model().objects.create_user(email=email, password=password)

def create_tag(user, name):
    return Tag.objects.create(user=user, name=name)


class PublicTagsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_tags_list(self):
        tags = [create_tag(self.user, 'tag1'), create_tag(self.user, 'tag2')]
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = TagSerializer(reversed(tags), many=True).data

        self.assertEqual(res.data, data)

    def test_tags_limited_to_user(self):
        user2 = create_user('user2@example.com')
        create_tag(user2, 'tag1')
        tags = [create_tag(self.user, 'tag2'), create_tag(self.user, 'tag3')]

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = TagSerializer(reversed(tags), many=True).data

        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, data)

    def test_update_tag(self):
        tag = create_tag(self.user, 'tag1')
        payload = {'name': 'tag11111'}

        res = self.client.patch(detail_url(tag.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = create_tag(self.user, 'tag1')

        res = self.client.delete(detail_url(tag.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
