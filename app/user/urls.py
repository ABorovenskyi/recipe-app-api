from django.urls import path

from .views import CreateUserView, CreateTokenView, UpdateUserView

app_name = 'user'

urlpatterns = [
    path('create/', CreateUserView.as_view(), name='create'),
    path('token/', CreateTokenView.as_view(), name='token'),
    path('me/', UpdateUserView.as_view(), name='me'),
]
