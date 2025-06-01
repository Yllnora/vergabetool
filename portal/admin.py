from django.contrib import admin
from .models import Projekt, Teilnahmeantrag, Upload, User

@admin.register(Projekt)
class ProjektAdmin(admin.ModelAdmin):
    list_display = ('name', 'deadline')

@admin.register(Teilnahmeantrag)
class TeilnahmeantragAdmin(admin.ModelAdmin):
    list_display = ('firmenname', 'projekt', 'erstellt_am', 'gesamt_score')
    list_filter = ('projekt',)

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'uploaded_at')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
