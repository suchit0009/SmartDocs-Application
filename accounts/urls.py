from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import user_list_api

# app_name = 'accounts' 

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('api/users/', user_list_api, name='user_list_api'),
    path('accounts/change-password/', views.change_password, name='change_password'),
    path('accounts/profile/', views.update_profile, name='profile'),
]


