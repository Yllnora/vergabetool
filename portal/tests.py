from django.test import TestCase
from django.urls import reverse

from .models import Teilnahmeantrag, User

class AntragSearchTest(TestCase):
    def setUp(self):
        # create and login a Vergabestelle user
        self.user = User.objects.create_user(
            username='verg', password='pass', role='Vergabestelle'
        )
        self.client.login(username='verg', password='pass')
        # two sample entries
        self.a1 = Teilnahmeantrag.objects.create(
            firmenname="Firma A", adresse="A", ansprechpartner="A", email="a@a.de",
            wirtschaftliche_verknuepfungen="", insolvenz=False, straftat=False,
            fehlende_abgaben=False, berufshaftpflicht_vorhanden=False,
            umsatz_2023=100, umsatz_2022=90, umsatz_2021=80,
            is_brutto=True, steuer_satz=19,
            projektleitung="", team_groesse=1, zustandigkeit_bauleitung="",
            referenz_1="", referenz_2="", referenz_upload=None
        )
        self.a2 = Teilnahmeantrag.objects.create(
            firmenname="Firma B", adresse="B", ansprechpartner="B", email="b@b.de",
            wirtschaftliche_verknuepfungen="", insolvenz=False, straftat=False,
            fehlende_abgaben=False, berufshaftpflicht_vorhanden=False,
            umsatz_2023=200, umsatz_2022=180, umsatz_2021=160,
            is_brutto=True, steuer_satz=19,
            projektleitung="", team_groesse=1, zustandigkeit_bauleitung="",
            referenz_1="", referenz_2="", referenz_upload=None
        )

    def test_search_by_valid_id(self):
        url = reverse('antrag_liste') + f'?q={self.a1.pk}'
        resp = self.client.get(url)
        self.assertContains(resp, "Firma A")
        self.assertNotContains(resp, "Firma B")

    def test_search_with_non_numeric_q_shows_all(self):
        url = reverse('antrag_liste') + '?q=foo'
        resp = self.client.get(url)
        # non-numeric q → fallback to all entries
        self.assertContains(resp, "Firma A")
        self.assertContains(resp, "Firma B")
