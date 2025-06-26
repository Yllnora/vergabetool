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
    path('antrag/<int:pk>/pdf/', login_required(views.antrag_pdf), name='antrag_pdf'),
    path('antrag/<int:pk>/json/', login_required(views.antrag_json), name='antrag_json'),
    path('antrag/<int:pk>/zip/', login_required(views.antrag_zip), name='antrag_zip'),
    path('antrag/<int:pk>/bewerten/', views.antrag_bewerten, name='antrag_bewerten'),
    path('antrag/neu/', views.teilnahmeantrag_erstellen, name='teilnahmeantrag_erstellen'),
    path('antraege/', views.antrag_liste, name='antrag_liste'),
    path('antrag/<int:pk>/', views.antrag_detail, name='antrag_detail'),
    path('antraege/', login_required(views.antrag_liste), name='antrag_liste'),
    path('kriterien/', login_required(views.kriterien_liste), name='kriterien_liste'),       # Platzhalter‐View
    path('auswertung/start/', login_required(views.auswertung_starten), name='auswertung_starten'),  # Platzhalter‐View
    path('projekte/', views.projekt_liste, name='projekt_liste'),
    path('dashboard_vergabestelle/', views.dashboard_vergabestelle, name='dashboard_vergabestelle'),
    # path('api/projekt/<int:projekt_pk>/fragen/', views.projekt_fragen_api, name='projekt_fragen_api'),
    path('api/projekt/<int:pk>/fragen/', views.projekt_fragen_api, name='projekt_fragen_api'),
    path('antrag/<int:pk>/bewerten/', views.antrag_bewerten, name='antrag_bewerten'),
    path('bewertungen/', views.bewertungen_liste, name='bewertungen_liste'),
    path('bewertungen/<int:pk>/', views.bewertung_detail, name='bewertung_detail'),







]
