
# portal/tests/test_forms.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal

from portal.forms import UploadForm, TeilnahmeantragForm
from portal.models import Projekt

class UploadFormTest(TestCase):
    def test_empty_form_invalid(self):
        form = UploadForm(data={}, files={})
        self.assertFalse(form.is_valid())

    def test_clean_file_rejects_wrong_extension(self):
        file = SimpleUploadedFile("test.txt", b"data")
        form = UploadForm(data={}, files={"file": file})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_clean_file_accepts_pdf(self):
        file = SimpleUploadedFile("test.pdf", b"data")
        form = UploadForm(data={}, files={"file": file})
        self.assertTrue(form.is_valid())

class TeilnahmeantragFormTest(TestCase):
    def setUp(self):
        self.projekt = Projekt.objects.create(name="E2E Project", deadline="2100-01-01")
        self.client.login(username='selenium', password='pass')
    def test_empty_form_invalid(self):
        form = TeilnahmeantragForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('firmenname', form.errors)
    def test_valid_data(self):
        data = {
            'projekt': str(self.projekt.pk),
            'firmenname': 'TestFirma',
            'adresse': 'Musterstraße 1 12345 Stadt',
            'ansprechpartner': 'Max Mustermann',
            'email': 'test@example.com',
            'wirtschaftliche_verknuepfungen': '',
            'insolvenz': False,
            'straftat': False,
            'fehlende_abgaben': False,
            'berufshaftpflicht_vorhanden': False,
            'umsatz_2023': '1000.00',
            'umsatz_2022': '900.00',
            'umsatz_2021': '800.00',
            'is_brutto': True,
            'steuer_satz': '19.00',
            'projektleitung': 'Herr X',
            'team_groesse': '5',
            'zustandigkeit_bauleitung': '',
            'referenz_1': 'Projekt A',
            'referenz_2': '',
            # referenz_upload optional, skip
        }
        form = TeilnahmeantragForm(data=data)
        self.assertTrue(form.is_valid())