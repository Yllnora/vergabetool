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
            # Brutto/Netto
            'is_brutto': forms.CheckboxInput(),
            'steuer_satz': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'max': '100',
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie einen Steuersatz zwischen 0 und 100 ein')",
                'oninput': "this.setCustomValidity('')",
            }),

            # Pflichtfelder
            'firmenname': forms.TextInput(attrs={
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie den Firmennamen ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'adresse': forms.Textarea(attrs={
                'rows': 2, 'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie die Adresse ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'ansprechpartner': forms.TextInput(attrs={
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie den Ansprechpartner ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'email': forms.EmailInput(attrs={
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie eine gültige E-Mail-Adresse ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'wirtschaftliche_verknuepfungen': forms.Textarea(attrs={
                'rows': 3, 'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie die wirtschaftlichen Verknüpfungen ein')",
                'oninput': "this.setCustomValidity('')",
            }),

            # Umsätze
            'umsatz_2023': forms.NumberInput(attrs={
                'placeholder': 'z. B. 2500000 (€)', 'step': '0.01',
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie den Umsatz 2023 ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'umsatz_2022': forms.NumberInput(attrs={
                'placeholder': 'z. B. 2000000 (€)', 'step': '0.01',
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie den Umsatz 2022 ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'umsatz_2021': forms.NumberInput(attrs={
                'placeholder': 'z. B. 1500000 (€)', 'step': '0.01',
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie den Umsatz 2021 ein')",
                'oninput': "this.setCustomValidity('')",
            }),

            # Berufshaftpflicht
            'berufshaftpflicht_nachweis': forms.ClearableFileInput(attrs={
                'accept': '.pdf'
            }),

            # Projektsteuerung
            'projektleitung': forms.TextInput(attrs={
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie die Projektleitung ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'team_groesse': forms.NumberInput(attrs={
                'placeholder': 'z. B. 5', 'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie die Teamgröße ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'zustandigkeit_bauleitung': forms.TextInput(attrs={
                'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie die Zuständigkeit für die Bauleitung ein')",
                'oninput': "this.setCustomValidity('')",
            }),

            # Referenzen
            'referenz_1': forms.Textarea(attrs={
                'rows': 3, 'required': 'required',
                'oninvalid': "this.setCustomValidity('Bitte geben Sie mindestens eine Referenz ein')",
                'oninput': "this.setCustomValidity('')",
            }),
            'referenz_2': forms.Textarea(attrs={'rows': 3}),
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
        if s is None or s < 0 or s > 100:
            raise forms.ValidationError("Steuersatz muss zwischen 0 und 100 liegen.")
        return s

    def clean_berufshaftpflicht_nachweis(self):
        file = self.cleaned_data.get('berufshaftpflicht_nachweis')
        if file:
            name = file.name.lower()
            if not name.endswith('.pdf'):
                raise forms.ValidationError("Bitte laden Sie ein PDF-Dokument hoch.")
            if "versicherung" not in name and "haftpflicht" not in name:
                raise forms.ValidationError(
                    "Dateiname sollte z. B. 'Versicherungsnachweis.pdf' enthalten."
                )
        return file

    def clean_referenz_upload(self):
        file = self.cleaned_data.get('referenz_upload')
        if file:
            name = file.name.lower()
            if not name.endswith('.pdf'):
                raise forms.ValidationError("Nur PDF-Dateien sind erlaubt.")
            if "referenz" not in name and "projekt" not in name:
                raise forms.ValidationError(
                    "Bitte benennen Sie die Datei z. B. als 'Referenz_Projektname.pdf'."
                )
        return file
