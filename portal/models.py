from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

class Frage(models.Model):
    projekt = models.ForeignKey('Projekt', on_delete=models.CASCADE, related_name='fragen')
    text = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.projekt.name} – {self.text[:50]}…"


# Benutzer mit Rollen
class User(AbstractUser):
    ROLE_CHOICES = (
        ('Bieter', 'Bieter'),
        ('Vergabestelle', 'Vergabestelle'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


# Datei-Upload (z. B. von Bietern)
class Upload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.file.name}"

class Projekt(models.Model):
    name = models.CharField(max_length=200, help_text="Projektname")
    beschreibung = models.TextField(blank=True)
    deadline = models.DateField(help_text="Einsendeschluss für Anträge")
    # (Fügen Sie hier gern noch weitere Felder hinzu, z.B. Kategorie, Punkte‐Gewichtung, …)

    def __str__(self):
        return self.name


# Teilnahmeantrag (Teil 1–4)
class Teilnahmeantrag(models.Model):
    # The Bieter who submitted this Antrag
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Der Bieter, der diesen Antrag eingereicht hat"
    )
    firmenname = models.CharField(max_length=200)
    adresse = models.TextField()
    ansprechpartner = models.CharField(max_length=100)
    email = models.EmailField()
    wirtschaftliche_verknuepfungen = models.TextField(blank=True)

    # Ausschlussgründe
    insolvenz = models.BooleanField(default=False)
    straftat = models.BooleanField(default=False)
    fehlende_abgaben = models.BooleanField(default=False)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    projekt = models.ForeignKey(
        'Projekt',
        on_delete=models.PROTECT,
        help_text="Für welches Projekt reichen Sie diesen Antrag ein?"
    )

    # Teil 2 – Wirtschaftliche Leistungsfähigkeit
    umsatz_2023 = models.DecimalField(max_digits=12, decimal_places=2)
    umsatz_2022 = models.DecimalField(max_digits=12, decimal_places=2)
    umsatz_2021 = models.DecimalField(max_digits=12, decimal_places=2)

    # — NEW Gross/Net toggle & tax rate
    is_brutto = models.BooleanField(
        default=True,
        help_text="Ankreuzen, wenn der Umsatz Brutto (inkl. Steuer) angegeben ist."
    )
    steuer_satz = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('19.00'),
        help_text="Steuersatz in Prozent (z. B. 19.00 für 19%)."
    )

    # --- New scoring fields (0–10 each) ---
    score_anforderung1 = models.IntegerField(
        null=True, blank=True,
        help_text="Punkte (0–10) für Kriterium 1"
    )
    score_anforderung2 = models.IntegerField(
        null=True, blank=True,
        help_text="Punkte (0–10) für Kriterium 2"
    )
    # here other score fields can be added as needed

    gesamt_score = models.IntegerField(
        null=True, blank=True,
        help_text="Summenpunktzahl (auto-berechnet)"
    )

    def berechne_gesamt_score(self):
        total = 0
        count = 0
        for fld in ['score_anforderung1', 'score_anforderung2']:
            val = getattr(self, fld)
            if val is not None:
                total += val
                count += 1
        return total if count else None

    def save(self, *args, **kwargs):
        # Recalculate gesamt_score whenever scores change
        self.gesamt_score = self.berechne_gesamt_score()
        super().save(*args, **kwargs)

    berufshaftpflicht_vorhanden = models.BooleanField(default=False)
    berufshaftpflicht_nachweis = models.FileField(
        upload_to='nachweise/',
        blank=True, null=True
    )

    # Teil 3 – Team
    projektleitung = models.CharField(
        max_length=100,
        help_text="Name der Projektleitung"
    )
    team_groesse = models.IntegerField(
        help_text="Anzahl Mitarbeitende im Projektteam"
    )
    zustandigkeit_bauleitung = models.CharField(
        max_length=100,
        blank=True,
        help_text="Verantwortlich für Bauleitung"
    )

    # Teil 4 – Referenzen
    referenz_1 = models.TextField(help_text="Beschreibung eines Referenzprojekts")
    referenz_2 = models.TextField(
        blank=True,
        help_text="Optionales weiteres Referenzprojekt"
    )
    referenz_upload = models.FileField(
        upload_to='referenzen/',
        blank=True, null=True,
        help_text="Nur PDF zulässig"
    )

    erstellt_am = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firmenname} ({self.ansprechpartner})"

    @property
    def umsatz_netto(self):
        """
        If stored value is Brutto, strip out the tax.
        Otherwise, return the stored (Netto) value.
        """
        if self.is_brutto:
            return (
                self.umsatz_2023
                / (Decimal('1') + self.steuer_satz / Decimal('100'))
            ).quantize(Decimal('0.01'))
        return self.umsatz_2023

    @property
    def umsatz_brutto(self):
        """
        If stored value is Netto, add the tax.
        Otherwise, return the stored (Brutto) value.
        """
        if not self.is_brutto:
            return (
                self.umsatz_2023
                * (Decimal('1') + self.steuer_satz / Decimal('100'))
            ).quantize(Decimal('0.01'))
        return self.umsatz_2023
    
    @property
    def is_late(self):
        if self.projekt is None or self.projekt.deadline is None:
            return False
        return timezone.now().date() > self.projekt.deadline