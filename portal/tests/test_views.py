# portal/tests/test_views.py
from django.test import TestCase
from django.urls import reverse
from django.shortcuts import render
from portal.forms import TeilnahmeantragForm
from unittest.mock import patch

from portal.models import Teilnahmeantrag, User, Projekt
from django.test import Client

class AntragViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='bieter', password='pw', role='Bieter')
        self.projekt = Projekt.objects.create(name="projekt", deadline="2100-01-01")
        self.client.login(username='bieter', password='pw')

    def test_get_antrag_form(self):
        response = self.client.get(reverse('antrag'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')

    @patch('portal.models.Teilnahmeantrag.save')  # Mock the save method

    def test_post_antrag_displays_thank_you(self, mock_save):
        # Ensure the user is logged in
        self.client.login(username='bieter', password='pw')
        url = reverse('teilnahmeantrag_erstellen')
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
            # dynamic Frage fields if any: if Projekt.fragen exist, include keys 'frage_<pk>'
        }
        resp = self.client.post(url, data)
        self.assertRedirects(resp, reverse('danke'))
    def antrag(request):
        form = TeilnahmeantragForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            return render(request, 'portal/danke.html', {'message': 'Vielen Dank!'})
        return render(request, 'portal/antrag_form.html', {'form': form})
        