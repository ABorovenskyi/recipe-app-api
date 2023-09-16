from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'title', 'time_in_minutes', 'price', 'link', 'description')
        read_only_fields = ('id',)
