from django.urls import path, include, path
from login import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('userprofile/', views.user_profile, name='profile'),
    path('logout/', views.user_logout, name='logout'),
    path('wallet/',views.wallet,name="wallet"),
    path('buy/',views.buy,name="buy"),
    
]