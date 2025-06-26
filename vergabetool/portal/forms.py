from django import forms
from .models import Upload, Teilnahmeantrag, Projekt, Frage, Kriterium, Bewertung, User
from django.contrib.auth.forms import UserCreationForm

class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            name = file.name.lower()
            if not name.endswith(('.pdf', '.xlsx')):
                raise forms.ValidationError("Nur PDF- oder Excel-Dateien sind erlaubt.")
        return file

class TeilnahmeantragBewertungForm(forms.ModelForm):
    class Meta:
        model = Teilnahmeantrag
        fields = ['score_anforderung1', 'score_anforderung2']  # add more as needed
        widgets = {
            'score_anforderung1': forms.NumberInput(attrs={'min': 0, 'max': 10}),
            'score_anforderung2': forms.NumberInput(attrs={'min': 0, 'max': 10}),
        }


class TeilnahmeantragForm(forms.ModelForm):
    class Meta:
        model = Teilnahmeantrag
        fields = [
            # Teil 1
            'projekt',
            'firmenname',
            'adresse',
            'ansprechpartner',
            'email',
            'wirtschaftliche_verknuepfungen',
            'insolvenz',
            'straftat',
            'fehlende_abgaben',
            # Teil 2
            'umsatz_2023',
            'umsatz_2022',
            'umsatz_2021',
            'berufshaftpflicht_vorhanden',
            'berufshaftpflicht_nachweis',
            # Teil 3
            'projektleitung',
            'team_groesse',
            'zustandigkeit_bauleitung',
            # Teil 4
            'referenz_1',
            'referenz_2',
            'referenz_upload',
        ]
        widgets = {
            'projekt': forms.Select(),
            'adresse': forms.Textarea(attrs={'rows': 2}),
            'wirtschaftliche_verknuepfungen': forms.Textarea(attrs={'rows': 3}),
            'referenz_1': forms.Textarea(attrs={'rows': 3}),
            'referenz_2': forms.Textarea(attrs={'rows': 3}),
            'umsatz_2023': forms.NumberInput(attrs={'placeholder': 'z. B. 2500000 (€)'}),
            'umsatz_2022': forms.NumberInput(attrs={'placeholder': 'z. B. 2000000 (€)'}),
            'umsatz_2021': forms.NumberInput(attrs={'placeholder': 'z. B. 1500000 (€)'}),
            'team_groesse': forms.NumberInput(attrs={'placeholder': 'z. B. 5'}),
            'referenz_upload': forms.ClearableFileInput(attrs={'accept': '.pdf'}),
        }
        labels = {
            'team_groesse': 'Team-Größe',
            'wirtschaftliche_verknuepfungen': 'Wirtschaftliche Verknüpfungen',
        }
        help_texts = {
            'referenz_upload': 'Bitte nur PDF-Dateien hochladen',
            'umsatz_2023': 'Angabe in Euro (€)',
            'umsatz_2022': 'Angabe in Euro (€)',
            'umsatz_2021': 'Angabe in Euro (€)',
            'team_groesse': 'Anzahl der Personen im Projektteam',
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Accept user to pre-fill firmenname and adresse.
        Also dynamically add question fields for the selected Projekt.
        """
        self.user = user
        super().__init__(*args, **kwargs)

        # If no initial for firmenname/adresse provided by caller, fill from user profile:
        if not self.is_bound and user is not None:
            # adapt attribute names to your User model: company_name, street, postal_code, city, country
            initial = {}
            if hasattr(user, 'company_name') and user.company_name:
                initial['firmenname'] = user.company_name
            # combine address parts:
            parts = []
            if hasattr(user, 'street') and user.street:
                parts.append(user.street)
            city_parts = []
            if hasattr(user, 'postal_code') and user.postal_code:
                city_parts.append(user.postal_code)
            if hasattr(user, 'city') and user.city:
                city_parts.append(user.city)
            if city_parts:
                parts.append(" ".join(city_parts))
            if hasattr(user, 'country') and user.country:
                parts.append(user.country)
            if parts and 'adresse' not in self.initial:
                initial['adresse'] = ", ".join(parts)
            # apply initial if fields exist and not already in initial:
            for fname, val in initial.items():
                if fname in self.fields and not self.initial.get(fname):
                    self.initial[fname] = val

        # Determine the Projekt instance to load Fragen, both on GET (unbound) and POST (bound)
        projekt = None
        if self.is_bound:
            projekt_id = self.data.get('projekt')
            if projekt_id:
                try:
                    projekt = Projekt.objects.get(pk=projekt_id)
                except Projekt.DoesNotExist:
                    projekt = None
        else:
            if self.instance and getattr(self.instance, 'projekt', None):
                projekt = self.instance.projekt

        # Dynamically add fields for each Frage of the Projekt
        if projekt:
            for frage in projekt.fragen.all():
                field_name = f"frage_{frage.pk}"
                label = frage.text
                if frage.field_type == Frage.FIELD_TYPE_BOOLEAN:
                    self.fields[field_name] = forms.BooleanField(label=label, required=False)
                    if self.instance and isinstance(self.instance.antworten, dict):
                        existing = self.instance.antworten.get(str(frage.pk))
                        if existing is not None:
                            self.initial[field_name] = existing
                elif frage.field_type == Frage.FIELD_TYPE_TEXT:
                    self.fields[field_name] = forms.CharField(
                        label=label, required=False,
                        widget=forms.Textarea(attrs={'rows': 2})
                    )
                    if self.instance and isinstance(self.instance.antworten, dict):
                        existing = self.instance.antworten.get(str(frage.pk))
                        if existing is not None:
                            self.initial[field_name] = existing
                # add more types if needed

    def clean(self):
        cleaned_data = super().clean()
        projekt = cleaned_data.get('projekt')
        if projekt:
            antworten = {}
            for frage in projekt.fragen.all():
                key = f"frage_{frage.pk}"
                if key in cleaned_data:
                    antworten[str(frage.pk)] = cleaned_data.get(key)
            self.instance.antworten = antworten
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # instance.antworten already set in clean()
        if commit:
            instance.save()
        return instance

    def clean_berufshaftpflicht_nachweis(self):
        file = self.cleaned_data.get('berufshaftpflicht_nachweis')
        if file:
            name = file.name.lower()
            if not name.endswith('.pdf'):
                raise forms.ValidationError("Bitte laden Sie ein PDF-Dokument hoch.")
            if "versicherung" not in name and "haftpflicht" not in name:
                raise forms.ValidationError("Dateiname sollte z. B. 'Versicherungsnachweis.pdf' enthalten.")
        return file

    def clean_referenz_upload(self):
        file = self.cleaned_data.get('referenz_upload')
        if file:
            name = file.name.lower()
            if not name.endswith('.pdf'):
                raise forms.ValidationError("Nur PDF-Dateien sind erlaubt.")
            if "referenz" not in name and "projekt" not in name:
                raise forms.ValidationError("Bitte benennen Sie die Datei z. B. als 'Referenz_Projektname.pdf'.")
        return file


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    # Bieter-only fields; we’ll show/hide in template/JS or validate in clean()
    company_name = forms.CharField(label="Firmenname", required=False)
    street = forms.CharField(label="Straße", required=False)
    postal_code = forms.CharField(label="PLZ", required=False)
    city = forms.CharField(label="Stadt", required=False)
    country = forms.CharField(label="Land", required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role',
                  'company_name', 'street', 'postal_code', 'city', 'country']

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')
        # If Bieter, require those fields:
        if role == 'Bieter':
            missing = []
            for fld in ['company_name','street','postal_code','city','country']:
                if not cleaned.get(fld):
                    missing.append(fld)
            if missing:
                raise forms.ValidationError("Für Bieter bitte alle Profilfelder ausfüllen.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # Fields are set by form
        if commit:
            user.save()
        return user

class BewertungForm(forms.Form):
    def __init__(self, *args, antrag: Teilnahmeantrag = None, **kwargs):
        """
        Dynamically add fields for each Kriterium of antrag.projekt.
        Expect: Projekt has related_name 'kriterien' for its Kriterien objects,
        each with .pk and .text.
        """
        super().__init__(*args, **kwargs)
        self.antrag = antrag
        if antrag is None:
            return  # nothing to add

        # Load existing saved scores to pre-fill
        existing: dict = antrag.bewertungen_data or {}

        for kriterium in antrag.projekt.kriterien.order_by('id'):
            key = str(kriterium.pk)
            # IntegerField for punkte
            field_name_p = f"punkte_{key}"
            # Use required=False so blank is allowed
            initial_p = None
            entry = existing.get(key)
            if entry and isinstance(entry, dict):
                initial_p = entry.get('punkte')
            self.fields[field_name_p] = forms.IntegerField(
                label=kriterium.text,
                min_value=0, max_value=10,
                required=False,
                initial=initial_p,
                help_text="0–10"
            )

            # CharField for kommentar
            field_name_c = f"kommentar_{key}"
            initial_c = ''
            if entry and isinstance(entry, dict):
                initial_c = entry.get('kommentar', '')
            self.fields[field_name_c] = forms.CharField(
                label="",  # label can be empty or something like "Kommentar"
                required=False,
                initial=initial_c,
                widget=forms.TextInput(attrs={'placeholder': 'Kommentar (optional)'})
            )

    def save(self, antrag: Teilnahmeantrag):
        """
        Save or update Bewertung instances for this Antrag.
        """
        projekt = antrag.projekt
        # Optionally: delete old Bewertungen not in this set, or update existing
        # A simple approach: for each kriterium, update_or_create; and optionally remove others.
        saved_keys = []
        for kriterium in projekt.kriterien.all():
            key = str(kriterium.pk)
            p_val = self.cleaned_data.get(f"punkte_{key}")
            c_val = self.cleaned_data.get(f"kommentar_{key}", '').strip()
            if p_val is not None:
                # update existing or create new
                bewertung_obj, created = Bewertung.objects.update_or_create(
                    antrag=antrag,
                    kriterium=kriterium,
                    defaults={'punkte': p_val, 'kommentar': c_val}
                )
                saved_keys.append(bewertung_obj.pk)
        # Optionally: remove Bewertungen for this Antrag for Kriterien no longer present or set to None:
        # E.g.:
        # Projekt’s kriterium IDs:
        kriterium_ids = [k.pk for k in projekt.kriterien.all()]
        # Delete any Bewertung entries for this antrag with kriterium not in kriterium_ids or where cleaned_data had None
        # For instance:
        Bewertung.objects.filter(antrag=antrag).exclude(kriterium__pk__in=kriterium_ids).delete()
        return antrag    
