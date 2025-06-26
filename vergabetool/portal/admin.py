from django.contrib import admin
from .models import Projekt, Teilnahmeantrag, Upload, User, Frage, Kriterium, Bewertung

@admin.register(Projekt)
class ProjektAdmin(admin.ModelAdmin):
    list_display = ('name', 'deadline')
    search_fields = ('name',)

@admin.register(Teilnahmeantrag)
class TeilnahmeantragAdmin(admin.ModelAdmin):
    list_display = ('firmenname','ansprechpartner','projekt','erstellt_am')
    list_filter = ('projekt',)
    search_fields = ('firmenname','ansprechpartner')

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'uploaded_at')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')

@admin.register(Kriterium)
class KriteriumAdmin(admin.ModelAdmin):
    list_display = ('text', 'projekt', 'max_punkte')
    list_filter = ('projekt',)
    search_fields = ('text',)

# If you want to see Bewertungen inline under Antrag in admin:
class BewertungInline(admin.TabularInline):
    model = Bewertung
    extra = 0

@admin.register(Frage)
class FrageAdmin(admin.ModelAdmin):
    list_display = ('projekt', 'text', 'field_type', 'order')
    list_filter = ('projekt', 'field_type')
    ordering = ('projekt', 'order')