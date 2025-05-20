# portal/tests/test_end2end.py
from django.test import LiveServerTestCase, override_settings
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By

from portal.models import User

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
        cls.browser = webdriver.Chrome()
        cls.user = User.objects.create_user(username='selenium', password='pass', role='Bieter')

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
        self.browser.get(self.live_server_url + reverse('antrag'))
        # Fill fields
        self.browser.find_element(By.NAME, "firmenname").send_keys("Firma X")
        self.browser.find_element(By.NAME, "adresse").send_keys("Str. 1\nCity")
        self.browser.find_element(By.NAME, "ansprechpartner").send_keys("Kontakt")
        self.browser.find_element(By.NAME, "email").send_keys("test@example.com")
        self.browser.find_element(By.NAME, "umsatz_2023").send_keys("100")
        self.browser.find_element(By.NAME, "umsatz_2022").send_keys("200")
        self.browser.find_element(By.NAME, "umsatz_2021").send_keys("300")
        self.browser.find_element(By.NAME, "projektleitung").send_keys("Leitung")
        self.browser.find_element(By.NAME, "team_groesse").send_keys("5")
        self.browser.find_element(By.NAME, "referenz_1").send_keys("Ref1")
        # Submit
        self.browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        # Verify thank-you
        current = self.browser.current_url.replace(self.live_server_url, '').rstrip('/')
        self.assertEqual(current, reverse('danke').rstrip('/'))
        heading = self.browser.find_element(By.TAG_NAME, "h2").text
        self.assertIn("Vielen Dank!", heading)
