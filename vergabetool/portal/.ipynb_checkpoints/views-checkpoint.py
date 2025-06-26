from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
import zipfile
import io
import os
from django.utils.text import slugify

from .models import User, Upload, Teilnahmeantrag
from .forms import UploadForm, TeilnahmeantragForm


def welcome(request):
    return render(request, 'portal/welcome.html')


def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        user = User.objects.create_user(username=username, email=email, password=password, role=role)
        messages.success(request, 'Registrierung erfolgreich! Bitte einloggen.')
        return redirect('login')
    return render(request, 'portal/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Login fehlgeschlagen. Bitte überprüfe deine Daten.')
    return render(request, 'portal/login.html')


@login_required
def user_dashboard(request):
    if request.user.role == 'Bieter':
        uploads = Upload.objects.filter(user=request.user).order_by('-uploaded_at')
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES.get('file')
                if uploaded_file:
                    if not uploaded_file.name.lower().endswith(('.pdf', '.xlsx')):
                        messages.error(request, 'Nur PDF- und Excel-Dateien erlaubt.')
                        return redirect('dashboard')
                upload = form.save(commit=False)
                upload.user = request.user
                upload.save()
                messages.success(request, 'Datei erfolgreich hochgeladen!')
                return redirect('dashboard')
        else:
            form = UploadForm()
        return render(request, 'portal/dashboard_bieter.html', {
            'form': form,
            'uploads': uploads
        })

    elif request.user.role == 'Vergabestelle':
        return render(request, 'portal/dashboard_vergabe.html')


def user_logout(request):
    logout(request)
    return redirect('login')


def teilnahmeantrag_erstellen(request):
    if request.method == 'POST':
        form = TeilnahmeantragForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('danke')
    else:
        form = TeilnahmeantragForm()
    return render(request, 'portal/teilnahmeantrag_form.html', {'form': form})


def danke(request):
    return render(request, 'portal/danke.html')


@login_required
def antrag_liste(request):
    if request.user.role == 'Vergabestelle':
        antraege = Teilnahmeantrag.objects.all().order_by('-erstellt_am')
        return render(request, 'portal/antrag_liste.html', {'antraege': antraege})
    else:
        return redirect('dashboard')


@login_required
def antrag_detail(request, pk):
    if request.user.role == 'Vergabestelle':
        antrag = get_object_or_404(Teilnahmeantrag, pk=pk)
        return render(request, 'portal/antrag_detail.html', {
            'antrag': antrag,
            'bewertung': "Bewertung folgt…"  # Platzhalter
        })
    else:
        return redirect('dashboard')


@login_required
def antrag_pdf(request, pk):
    return HttpResponse("PDF-Export ist aktuell deaktiviert, da WeasyPrint fehlt.")


@login_required
def antrag_zip(request, pk):
    return HttpResponse("ZIP-Export ist aktuell deaktiviert, da PDF-Funktion nicht verfügbar ist.")


@login_required
def antrag_json(request, pk):
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')
    
    antrag = get_object_or_404(Teilnahmeantrag, pk=pk)
    data = {
        "firmenname": antrag.firmenname,
        "ansprechpartner": antrag.ansprechpartner,
        "email": antrag.email,
        "adresse": antrag.adresse,
        "umsatz": {
            "2023": float(antrag.umsatz_2023),
            "2022": float(antrag.umsatz_2022),
            "2021": float(antrag.umsatz_2021)
        },
        "berufshaftpflicht": antrag.berufshaftpflicht_vorhanden,
        "erstellt_am": antrag.erstellt_am.isoformat(),
    }
    return JsonResponse(data)
