from django.urls import path, include, path
from login import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
]