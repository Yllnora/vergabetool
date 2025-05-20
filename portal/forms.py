from django import forms
from .models import Upload, Teilnahmeantrag

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

class TeilnahmeantragForm(forms.ModelForm):
    class Meta:
        model = Teilnahmeantrag
        fields = [
            # Teil 1
            'is_brutto',
            'steuer_satz',
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
        help_texts = {
            'referenz_upload': 'Bitte nur PDF-Dateien hochladen',
            'umsatz_2023': 'Angabe in Euro (€)',
            'umsatz_2022': 'Angabe in Euro (€)',
            'umsatz_2021': 'Angabe in Euro (€)',
            'team_groesse': 'Anzahl der Personen im Projektteam',
        }

    def clean_steuer_satz(self):
        s = self.cleaned_data.get('steuer_satz')
        if s < 0 or s > 100:
            raise forms.ValidationError("Steuersatz muss zwischen 0 und 100 liegen.")
        return s

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
