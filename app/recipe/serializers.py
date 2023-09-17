from rest_framework import serializers

from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'title', 'time_in_minutes', 'price', 'link', 'tags')
        read_only_fields = ('id',)

    def _get_or_create_tags(self, tags, recipe):
        user = self.context['request'].user

        for tag_obj in tags:
            tag, created = Tag.objects.get_or_create(user=user, **tag_obj)
            recipe.tags.add(tag)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe )

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('description',)
