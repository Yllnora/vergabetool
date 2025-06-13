from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

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


class Frage(models.Model):
    FIELD_TYPE_BOOLEAN = 'boolean'
    FIELD_TYPE_TEXT = 'text'
    FIELD_TYPE_CHOICES = [
        (FIELD_TYPE_BOOLEAN, 'Ja/Nein'),
        (FIELD_TYPE_TEXT, 'Freitext'),
        # you could extend: ('number', 'Zahl'), ('choice', 'Auswahl'), etc.
    ]

    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE, related_name='fragen')
    text = models.TextField(help_text="Die Fragestellung, z.B. 'Gab es besondere Anforderungen?'")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default=FIELD_TYPE_BOOLEAN)

    order = models.PositiveIntegerField(default=0, help_text="Reihenfolge der Fragen in Formular")
    # optional: add an ordering meta

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"[{self.projekt.name}] Frage #{self.pk}: {self.text[:30]}..."

class Kriterium(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE, related_name='kriterien')
    text = models.CharField(max_length=500, help_text="Beschreiben Sie das Kriterium")
    # Optional: allow varying max score, otherwise assume 10:
    max_punkte = models.PositiveSmallIntegerField(default=10, help_text="Maximale Punktzahl (z. B. 10)")
    # Optional: weight, description, etc.
    def __str__(self):
        return f"{self.projekt.name}: {self.text[:30]}{'…' if len(self.text)>30 else ''}"

# Teilnahmeantrag (Teil 1–4)
class Teilnahmeantrag(models.Model):
    # The Bieter who submitted this Antrag
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Der Bieter, der diesen Antrag eingereicht hat"
    )
    projekt = models.ForeignKey(Projekt, on_delete=models.PROTECT, related_name='antraege')

    firmenname = models.CharField(max_length=200)
    adresse = models.CharField(max_length=200)
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


    # NEW: dynamic answers to Fragen
    from django.db.models import JSONField
    antworten = JSONField(blank=True, default=dict, help_text="Speichert die Antworten auf projektspezifische Fragen als JSON")

    erstellt_am = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.firmenname} ({self.ansprechpartner})"

class Bewertung(models.Model):
    antrag = models.ForeignKey(Teilnahmeantrag, on_delete=models.CASCADE, related_name='bewertungen')
    kriterium = models.ForeignKey(Kriterium, on_delete=models.CASCADE, related_name='bewertungen')
    punkte = models.PositiveSmallIntegerField()
    kommentar = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('antrag', 'kriterium')  # one score per criterion per application

    def __str__(self):
        return f"{self.antrag} - {self.kriterium.text[:20]}: {self.punkte}"

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
        """
        Compare submission date to the project's deadline.
        Return True if submitted after deadline.
        """
        if not self.projekt or not self.projekt.deadline:
            return False  # or decide default
        return self.erstellt_am.date() > self.projekt.deadline