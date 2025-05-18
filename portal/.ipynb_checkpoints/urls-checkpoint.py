from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='home'),  # ← ersetzt login
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
]
