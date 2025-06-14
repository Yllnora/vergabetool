from django import forms
from .models import Upload, Teilnahmeantrag, Projekt, Frage, Kriterium, Bewertung

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
            'umsatz_2023': forms.NumberInput(attrs={'placeholder': 'z. B. 2500000 (€)'}),
            'umsatz_2022': forms.NumberInput(attrs={'placeholder': 'z. B. 2000000 (€)'}),
            'umsatz_2021': forms.NumberInput(attrs={'placeholder': 'z. B. 1500000 (€)'}),
            'team_groesse': forms.NumberInput(attrs={'placeholder': 'z. B. 5'}),
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
            'team_größe': 'Anzahl der Personen im Projektteam',
        }

    def __init__(self, *args, **kwargs):
        """
        Dynamically add fields for each Frage of the selected Projekt.
        On GET: if editing instance with a projekt, or if initial data contains projekt,
          add those fields so template can render them.
        On POST: self.data has 'projekt', so we add fields before validation.
        """
        super().__init__(*args, **kwargs)

        projekt = None
        # 1) If bound form, get projekt from data
        if self.is_bound:
            projekt_id = self.data.get('projekt')
            if projekt_id:
                try:
                    projekt = Projekt.objects.get(pk=projekt_id)
                except Projekt.DoesNotExist:
                    projekt = None
        else:
            # Not bound: maybe editing existing instance
            if self.instance and getattr(self.instance, 'projekt', None):
                projekt = self.instance.projekt

        # If we have a projekt, fetch its Fragen and add corresponding form fields
        if projekt:
            fragen_qs = projekt.fragen.all()
            for frage in fragen_qs:
                field_name = f"frage_{frage.pk}"
                label = frage.text
                if frage.field_type == Frage.FIELD_TYPE_BOOLEAN:
                    self.fields[field_name] = forms.BooleanField(
                        label=label,
                        required=False
                    )
                    
                    if self.instance and isinstance(self.instance.antworten, dict):
                        existing = self.instance.antworten.get(str(frage.pk))
                        
                        if existing is not None:
                            self.initial[field_name] = existing
                elif frage.field_type == Frage.FIELD_TYPE_TEXT:
                    self.fields[field_name] = forms.CharField(
                        label=label,
                        required=False,
                        widget=forms.Textarea(attrs={'rows': 2})
                    )
                    if self.instance and isinstance(self.instance.antworten, dict):
                        existing = self.instance.antworten.get(str(frage.pk))
                        if existing is not None:
                            self.initial[field_name] = existing
                else:
                    
                    pass

    def clean(self):
        """
        Collect dynamic question answers into a dict and assign to instance.antworten.
        """
        cleaned_data = super().clean()
        projekt = cleaned_data.get('projekt')
        if projekt:
            antworten = {}
            # For each Frage of that projekt, pick out cleaned_data[f"frage_{id}"]
            for frage in projekt.fragen.all():
                key = f"frage_{frage.pk}"
                # If field wasn't added to form (e.g. invalid projekt), skip
                if key in self.fields:
                    antworten[str(frage.pk)] = cleaned_data.get(key)
            # Attach to instance
            self.instance.antworten = antworten
        return cleaned_data

    def save(self, commit=True):
        """
        Ensure instance.user is set by view before save.
        The dynamic antworten JSON was set in clean().
        """
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
                raise forms.ValidationError("Dateiname sollte z. B. 'Versicherungsnachweis.pdf' enthalten.")
        return file

    def clean_referenz_upload(self):
        file = self.cleaned_data.get('referenz_upload')
        if file:
            name = file.name.lower()
            if not name.endswith('.pdf'):
                raise forms.ValidationError("Nur PDF-Dateien sind erlaubt.")
            if "referenz" not in name and "projekt" not in name:
                raise forms.ValidationError("Bitte benennen Sie die Datei z. B. als 'Referenz_Projektname.pdf'.")
        return file

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
