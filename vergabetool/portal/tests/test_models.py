# portal/tests/test_models.py
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from portal.models import User, Teilnahmeantrag, Projekt, Upload

class UserModelTest(TestCase):
    def test_role_can_be_choice(self):
        u = User.objects.create_user(
            username="alice",
            password="secret",
            role="Bieter"
        )
        self.assertEqual(u.role, "Bieter")

    def test_invalid_role_raises(self):
        u = User(username="bob", role="NotAValidRole")
        with self.assertRaises(ValidationError):
            u.full_clean()

class UploadModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="uploader",
            password="pwd",
            role="Bieter"
        )

    def test_upload_saves_file(self):
        dummy = SimpleUploadedFile("doc.pdf", b"content")
        upload = Upload.objects.create(user=self.user, file=dummy)
        self.assertEqual(upload.user, self.user)
        self.assertTrue(upload.file.name.endswith(".pdf"))

class TeilnahmeantragModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pwd", role="Bieter")
        self.projekt = Projekt.objects.create(name="P1", deadline="2100-01-01")
    def test_str_returns_firmenname_and_ansprechpartner(self):
        t = Teilnahmeantrag.objects.create(
            user=self.user,
            projekt=self.projekt,
            firmenname="Müller GmbH", adresse="Hauptstraße 1\n12345 Stadt",
            ansprechpartner="Frau Müller", email="mueller@example.com",
            wirtschaftliche_verknuepfungen="keine",
            insolvenz=False, straftat=False, fehlende_abgaben=False,
            berufshaftpflicht_vorhanden=False,
            umsatz_2023=Decimal('1000.00'), umsatz_2022=Decimal('900.00'),
            umsatz_2021=Decimal('800.00'), is_brutto=True, steuer_satz=Decimal('19.00'),
            projektleitung="Herr Schmidt", team_groesse=10,
            zustandigkeit_bauleitung="Bauleiter A",
            referenz_1="Projekt X", referenz_2="", referenz_upload=None
        )
        self.assertEqual(str(t), "Müller GmbH (Frau Müller)")

    def test_umsatz_netto_brutto_properties(self):
        t1 = Teilnahmeantrag.objects.create(
            user=self.user,
            projekt=self.projekt,
            firmenname="Test", adresse="A\nB",
            ansprechpartner="X", email="x@y.de", wirtschaftliche_verknuepfungen="",
            insolvenz=False, straftat=False, fehlende_abgaben=False,
            berufshaftpflicht_vorhanden=False,
            umsatz_2023=Decimal('1000.00'), umsatz_2022=Decimal('900.00'),
            umsatz_2021=Decimal('800.00'), is_brutto=True, steuer_satz=Decimal('19.00'),
            projektleitung="P", team_groesse=1,
            zustandigkeit_bauleitung="Z", referenz_1="R1",
            referenz_2="", referenz_upload=None
        )
        self.assertEqual(t1.umsatz_netto, Decimal('840.34'))
        self.assertEqual(t1.umsatz_brutto, Decimal('1000.00'))

        t2 = Teilnahmeantrag.objects.create(
            user=self.user,
            projekt=self.projekt,
            firmenname="Test", adresse="A\nB",
            ansprechpartner="X", email="x@y.de", wirtschaftliche_verknuepfungen="",
            insolvenz=False, straftat=False, fehlende_abgaben=False,
            berufshaftpflicht_vorhanden=False,
            umsatz_2023=Decimal('1000.00'),
            umsatz_2022=Decimal('900.00'), umsatz_2021=Decimal('800.00'),
            is_brutto=False, steuer_satz=Decimal('19.00'),
            projektleitung="P", team_groesse=1,
            zustandigkeit_bauleitung="Z", referenz_1="R1",
            referenz_2="", referenz_upload=None
        )
        self.assertEqual(t2.umsatz_netto, Decimal('1000.00'))
        self.assertEqual(t2.umsatz_brutto, Decimal('1190.00'))