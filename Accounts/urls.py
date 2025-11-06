from . import views
from django.urls import path, include

urlpatterns = [
    path('profiles/<str:username>/', views.user_profile, name='user_profile'),
    path('profiles/', views.profiles, name="profiles"),
]