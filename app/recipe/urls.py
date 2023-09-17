from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet, IngredientView

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredient', IngredientView)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]