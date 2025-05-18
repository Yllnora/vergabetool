from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Öffentlich zugänglich
    path('', views.welcome, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Geschützt: Nur nach Login erreichbar
    path('dashboard/', login_required(views.user_dashboard), name='dashboard'),
    path('antrag/', login_required(views.teilnahmeantrag_erstellen), name='antrag'),
    path('danke/', login_required(views.danke), name='danke'),

    path('antraege/', login_required(views.antrag_liste), name='antrag_liste'),
    path('antraege/<int:pk>/', login_required(views.antrag_detail), name='antrag_detail'),

    path('antrag/<int:pk>/pdf/', login_required(views.antrag_pdf), name='antrag_pdf'),
    path('antrag/<int:pk>/json/', login_required(views.antrag_json), name='antrag_json'),
    path('antrag/<int:pk>/zip/', login_required(views.antrag_zip), name='antrag_zip'),
]
