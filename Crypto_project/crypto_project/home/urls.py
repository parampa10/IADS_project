from django.urls import path, include, path
from home import views

urlpatterns = [
    path('', views.index, name='index'),
]