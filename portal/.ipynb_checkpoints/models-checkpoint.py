from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('Bieter', 'Bieter'),
        ('Vergabestelle', 'Vergabestelle'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Upload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.file.name}"
