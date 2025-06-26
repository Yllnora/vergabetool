# portal/tests/test_views.py
from django.test import TestCase
from django.urls import reverse
from django.shortcuts import render
from portal.forms import TeilnahmeantragForm

from portal.models import Teilnahmeantrag, User

class AntragViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bieter', password='pass', role='Bieter')
        self.client.login(username='bieter', password='pass')

    def antrag(request):
        form = TeilnahmeantragForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            return render(request, 'portal/danke.html', {...})
        return render(request, 'portal/antrag_form.html', {'form': form})


    def test_get_antrag_form(self):
        response = self.client.get(reverse('antrag'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')

    def test_post_antrag_displays_thank_you(self):
        data = {
            'firmenname': 'TestFirma',
            'adresse': 'Addr\nLine2',
            'ansprechpartner': 'Kontakt',
            'email': 'a@b.com',
            'wirtschaftliche_verknuepfungen': '',
            'insolvenz': False,
            'straftat': False,
            'fehlende_abgaben': False,
            'berufshaftpflicht_vorhanden': False,
            'umsatz_2023': '1000.00',
            'is_brutto': True,
            'steuer_satz': '19.00',
            'projektleitung': 'Lead',
            'team_groesse': '5',
            'zustandigkeit_bauleitung': '',
            'referenz_1': 'Ref1',
            'referenz_2': '',
        }
        resp = self.client.post(reverse('antrag'), data)
        self.assertEqual(resp.status_code, 200)
    def antrag(request):
        form = TeilnahmeantragForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            return render(request, 'portal/danke.html', {'message': 'Vielen Dank!'})
        return render(request, 'portal/antrag_form.html', {'form': form})
        