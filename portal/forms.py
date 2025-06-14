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
    """
    Dynamically built: fields will be added in the view for each Kriterium of the Projekt.
    Field names: f"punkte_{k_id}", optional f"kommentar_{k_id}".
    """

    def __init__(self, *args, antrag=None, **kwargs):
        """
        antrag: the Teilnahmeantrag instance to score.
        """
        super().__init__(*args, **kwargs)
        if antrag is None:
            return
        projekt = antrag.projekt
        if not projekt:
            return
        # Fetch all criteria for this projekt
        kriterien = Kriterium.objects.filter(projekt=projekt).order_by('id')
        # If existing Bewertungen exist, build a dict for initial values:
        existing = {b.kriterium_id: b for b in antrag.bewertungen.all()}
        for kriterium in kriterien:
            field_name = f"punkte_{kriterium.pk}"
            max_p = kriterium.max_punkte or 10
            initial_punkte = existing.get(kriterium.pk).punkte if kriterium.pk in existing else None
            self.fields[field_name] = forms.IntegerField(
                label=kriterium.text,
                min_value=0,
                max_value=max_p,
                initial=initial_punkte,
                required=True,
                help_text=f"0 bis {max_p}"
            )
            # Optional: comment field
            comment_field = f"kommentar_{kriterium.pk}"
            init_comment = existing.get(kriterium.pk).kommentar if kriterium.pk in existing else ''
            self.fields[comment_field] = forms.CharField(
                label=f"Kommentar zu „{kriterium.text[:30]}“",
                initial=init_comment,
                required=False,
                widget=forms.Textarea(attrs={'rows': 2})
            )

    def save(self, antrag):
        """
        Read cleaned_data and create/update Bewertung instances for this Antrag.
        """
        # For each field in cleaned_data, find those starting with 'punkte_'
        for name, value in self.cleaned_data.items():
            if name.startswith("punkte_"):
                _, k_id_str = name.split("_", 1)
                try:
                    k_id = int(k_id_str)
                except ValueError:
                    continue
                punkte = value
                # find comment:
                comment_key = f"kommentar_{k_id}"
                kommentar = self.cleaned_data.get(comment_key, "")
                kriterium = Kriterium.objects.get(pk=k_id)
                bewertung_obj, created = Bewertung.objects.update_or_create(
                    antrag=antrag, kriterium=kriterium,
                    defaults={'punkte': punkte, 'kommentar': kommentar}
                )
        # Optionally return something
        return
