# portal/tests/test_end2end.py
from django.test import LiveServerTestCase, override_settings
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from portal.models import User, Projekt
from datetime import date
from datetime import timedelta

@override_settings(
    MEDIA_ROOT='/tmp/media',
    STATIC_ROOT='/tmp/static',
    STATIC_URL='/static/',
    MEDIA_URL='/media/',
    DEBUG=True
)
class AntragE2ETest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')            # run in headless mode
        options.add_argument('--disable-gpu')         # disable GPU (often needed)
        options.add_argument('--no-sandbox')          # disable sandbox (in some CI)
        options.add_argument('--window-size=1920,1080')
        # you may need other flags depending on environment
        cls.browser = webdriver.Chrome(options=options)
        cls.user = User.objects.create_user(username='selenium', password='pass', role='Bieter')
        # Create a project for the test
        Projekt.objects.create(name="E2E Project", deadline=date(2100, 1, 1))

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_full_flow(self):
        # Log in
        self.browser.get(self.live_server_url + reverse('login'))
        self.browser.find_element(By.NAME, "username").send_keys("selenium")
        self.browser.find_element(By.NAME, "password").send_keys("pass")
        self.browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        # Navigate to form
        self.browser.get(self.live_server_url + reverse('teilnahmeantrag_erstellen'))
        # Fill fields
        Projekt.objects.create(name="E2E Project", deadline=date(2100,1,1))
        # later they create again with deadline date.today()+7
        select = Select(self.browser.find_element(By.NAME, "projekt"))
        select.select_by_visible_text("E2E Project") 
        self.browser.find_element(By.NAME, "firmenname").send_keys("TestFirma")
        self.browser.find_element(By.NAME, "adresse").send_keys("Musterstraße 1 12345 Stadt")
        self.browser.find_element(By.NAME, "ansprechpartner").send_keys("Max Mustermann")
        self.browser.find_element(By.NAME, "email").send_keys("test@example.com")
        self.browser.find_element(By.NAME, "umsatz_2023").send_keys("1000.00")
        self.browser.find_element(By.NAME, "umsatz_2022").send_keys("900.00")
        self.browser.find_element(By.NAME, "umsatz_2021").send_keys("800.00")
        self.browser.find_element(By.NAME, "projektleitung").send_keys("Herr X")
        self.browser.find_element(By.NAME, "team_groesse").send_keys("5")
        self.browser.find_element(By.NAME, "referenz_1").send_keys("Projekt A")
        # Submit
        self.browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        # Verify thank-you
        current = self.browser.current_url.replace(self.live_server_url, '').rstrip('/')
        self.assertEqual(current, reverse('danke').rstrip('/'))
        heading = self.browser.find_element(By.TAG_NAME, "h2").text
        self.assertIn("Vielen Dank!", heading)
