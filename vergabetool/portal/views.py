from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg, Count, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Max
from django.utils import timezone
from .forms import UserRegisterForm, UploadForm, TeilnahmeantragForm, BewertungForm
import string

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.text import slugify

from .models import User, Upload, Teilnahmeantrag, Projekt, Frage, Kriterium, Bewertung
from .forms import UploadForm, TeilnahmeantragForm, TeilnahmeantragBewertungForm, BewertungForm


def welcome(request):
    # Umleitung auf Login, falls Nutzer schon eingeloggt ist
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'portal/welcome.html')



def user_register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registrierung erfolgreich! Bitte einloggen.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'portal/register.html', {'form': form})


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
def dashboard_vergabestelle(request):
    """
    Zeigt für die Vergabestelle eine Übersicht aller Projekte:
      - Anzahl der eingegangenen Anträge
      - Durchschnittsumsatz 2023 pro Projekt
      - Gesamtsumme aller Anträge pro Projekt
      - (optional) Top-Bieter
    """
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')

    # 1) Holen wir uns alle Projekte:
    alle_projekte = Projekt.objects.all()

    # 2) Annotate = zählen wir alle Anträge pro Projekt, plus Durchschnitt/Umsatz
    projekte_mit_stats = alle_projekte.annotate(
        anzahl_antraege=Count('teilnahmeantrag'),
        avg_umsatz_2023=Avg('teilnahmeantrag__umsatz_2023'),
        sum_umsatz_2023=Sum('teilnahmeantrag__umsatz_2023'),
    ).order_by('deadline')

    return render(request, 'portal/dashboard_vergabe.html', {
        'projekte_stats': projekte_mit_stats,
        # 'heute': timezone.now().date()  # falls noch benötigt
    })

@login_required
def user_dashboard(request):
    # Initialize variables so Pylance knows they exist
    form = None
    meine_antraege = None

    if request.user.role == 'Bieter':
        # Fetch existing uploads and Anträge for this Bieter
        uploads = Upload.objects.filter(user=request.user).order_by('-uploaded_at')
        meine_antraege = Teilnahmeantrag.objects.filter(
            user=request.user
        ).order_by('-erstellt_am')

        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES.get('file')
                if uploaded_file and not uploaded_file.name.lower().endswith(('.pdf', '.xlsx')):
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
            'uploads': uploads,
            'meine_antraege': meine_antraege,  # pass the user’s Anträge
        })

    elif request.user.role == 'Vergabestelle':
        # Fetch all Projekte, order by deadline, and prefetch each Projekt’s Anträge
        alle_projekte = Projekt.objects.all().order_by('deadline').prefetch_related('teilnahmeantrag_set')
        return render(request, 'portal/dashboard_vergabe.html', {
            'projekte': alle_projekte
        })

    # (If for some reason role is neither, you might redirect or raise PermissionDenied)
    return redirect('login')


@login_required
def projekt_liste(request):
    """
    Zeigt alle Projekte (mit Deadline) und darunter jeweils die eingereichten Anträge.
    Nur ein Benutzer mit role='Vergabestelle' darf diese Seite sehen.
    """
    # 1) Zugriffsschutz: Nur Vergabestelle darf auf diese View
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')

    # 2) Alle Projekte nach Deadline sortieren
    #    -> select_related ist hier nicht nötig, weil wir auf den FK antrags‐seite zugreifen
    #    -> prefetch_related lädt alle zugehörigen Teilnahmeantrag‐Sets in einem Rutsch
    alle_projekte = Projekt.objects.order_by('deadline')\
        .prefetch_related('teilnahmeantrag_set')
    # 3) Rendern der Template mit dem Context
    return render(request, 'portal/projekt_liste.html', {
        'projekte': alle_projekte
    })


@login_required
def antrag_index(request):
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')

    # Build a dict: { 'A': queryset_of_Anfragen_starting_with_A, 'B': … }
    grouped = {}
    for letter in string.ascii_uppercase:
        qs = Teilnahmeantrag.objects.filter(
            firmenname__istartswith=letter
        ).order_by('firmenname')
        grouped[letter] = qs

    return render(request, 'portal/antrag_index.html', {
        'grouped': grouped
    })


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def teilnahmeantrag_erstellen(request):
    if request.user.role != 'Bieter':
        return redirect('dashboard')

    # Prepare initial dict from user profile if desired; 
    # but since form __init__ handles initial from user, you may omit passing initial here.
    initial = {}
    # (Optional) you could compute initial here, but form __init__ already does it.

    if request.method == 'POST':
        form = TeilnahmeantragForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            antrag = form.save(commit=False)
            antrag.user = request.user
            antrag.save()
            return redirect('danke')
    else:
        form = TeilnahmeantragForm(user=request.user)
    return render(request, 'portal/teilnahmeantrag_form.html', {'form': form})


@login_required
def antrag_bewerten(request, pk):
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')
    antrag = get_object_or_404(Teilnahmeantrag, pk=pk)
    projekt = antrag.projekt
    if not projekt:
        messages.error(request, "Dieser Antrag hat kein zugeordnetes Projekt.")
        return redirect('antrag_detail', pk=pk)
    if not projekt.kriterien.exists():
        messages.info(request, "Für dieses Projekt wurden noch keine Kriterien definiert.")
        return redirect('antrag_detail', pk=pk)

    if request.method == 'POST':
        form = BewertungForm(request.POST, antrag=antrag)
        if form.is_valid():
            form.save(antrag)
            messages.success(request, "Bewertung gespeichert.")
            return redirect('antrag_detail', pk=antrag.pk)
    else:
        form = BewertungForm(antrag=antrag)

    # Prepare pairs for template if you prefer that style
    kriterium_pairs = []
    for kriterium in projekt.kriterien.order_by('id'):
        key = str(kriterium.pk)
        punkte_field = form[f"punkte_{key}"]
        comment_field = form[f"kommentar_{key}"]
        kriterium_pairs.append({
            'label': kriterium.text,
            'punkte_field': punkte_field,
            'comment_field': comment_field,
        })

    return render(request, 'portal/antrag_bewertung.html', {
        'antrag': antrag,
        'form': form,
        'kriterium_pairs': kriterium_pairs,
    })



@login_required
def danke(request):
    return render(request, 'portal/danke.html')

@login_required
def projekt_fragen_api(request, pk):
    """
    Return JSON list of Fragen for Projekt with id=pk.
    Each item: {id: <pk>, text: <text>, field_type: <'boolean' or 'text'>}
    """
    projekt = get_object_or_404(Projekt, pk=pk)
    fragen = projekt.fragen.all().values('pk', 'text', 'field_type')
    # convert QuerySet to list
    data = []
    for f in fragen:
        data.append({
            'id': f['pk'],
            'text': f['text'],
            'field_type': f['field_type'],
        })
    return JsonResponse({'fragen': data})

@login_required
def antrag_liste(request):
    # 1) Read the search term (if any)
    q = request.GET.get('q', '').strip()

    # 2) Start with all applications, ordered by newest first.
    #    select_related('projekt') avoids extra DB queries when checking projekt.deadline.
    base_qs = Teilnahmeantrag.objects.select_related('projekt').order_by('-erstellt_am')

    # 3) If the user provided a search term, filter by Firmenname OR adresse.
    if q:
        base_qs = base_qs.filter(
            Q(firmenname__icontains=q) |
            Q(adresse__icontains=q)
        )

    # 4) Split into on_time vs. late based on the project's deadline.
    today = timezone.now().date()

    # on_time: projekt.deadline >= today
    on_time = base_qs.filter(projekt__deadline__gte=today)

    # late: projekt.deadline < today
    late = base_qs.filter(projekt__deadline__lt=today)

    # 5) Pass both QuerySets plus the search term to the template
    return render(request, 'portal/antrag_liste.html', {
        'on_time': on_time,
        'late': late,
        'search_query': q,
    })

@login_required
def antrag_detail(request, pk):
    antrag = get_object_or_404(Teilnahmeantrag, pk=pk)
    # Berechtigung wie gehabt...
    raw = getattr(antrag, 'bewertungen_data', None)
    # Falls raw None oder {} oder leeres Dict: keine Bewertung
    has_bewertung = bool(raw)  # True nur, wenn raw ein nicht-leeres Dict ist
    bewertungen = raw if has_bewertung else {}
    kriterien = antrag.projekt.kriterien.all()
    return render(request, 'portal/antrag_detail.html', {
        'antrag': antrag,
        'bewertungen': bewertungen,
        'has_bewertung': has_bewertung,
        'kriterien': kriterien,
    })


@login_required
def bewertungen_liste(request):
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')
    # Find all Anträge that have ≥1 Bewertung, annotate with the latest timestamp:
    antraege = (
        Teilnahmeantrag.objects
        .filter(bewertungen__isnull=False)
        .annotate(letzte=Max('bewertungen__erstellt_am'))
        .order_by('-letzte')
        .distinct()
    )
    return render(request, 'portal/bewertungen_liste.html', {
        'antraege': antraege,
    })

@login_required
def bewertung_detail(request, pk):
    antrag = get_object_or_404(Teilnahmeantrag, pk=pk)
    if request.user.role != 'Vergabestelle':
        return redirect('dashboard')
    # Get all Kriterien for this project:
    kriterien = antrag.projekt.kriterien.all()
    # Fetch Bewertungen queryset:
    bewertungen_qs = antrag.bewertungen.select_related('kriterium').order_by('kriterium__id')
    # Build a dict {kriterium.pk: bewertung_obj} for template convenience:
    bewertungen_dict = { str(b.kriterium.pk): b for b in bewertungen_qs }
    return render(request, 'portal/bewertung_detail.html', {
        'antrag': antrag,
        'kriterien': kriterien,
        'bewertungen': bewertungen_dict,
    })



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
        "id": antrag.pk,
        "projekt": {
            "id": antrag.projekt.pk,
            "name": antrag.projekt.name,
            "deadline": antrag.projekt.deadline.isoformat() if antrag.projekt.deadline else None,
        },
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


@login_required
def kriterien_liste(request):
    return render(request, 'portal/coming_soon.html', {'message': 'Kriterienverwaltung folgt…'})

@login_required
def auswertung_starten(request):
    # Hier später die Logik anstoßen
    messages.info(request, 'Auswertung ist noch nicht implementiert.')
    return redirect('antrag_liste')
