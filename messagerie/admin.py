# messagerie/admin.py
from django.contrib import admin
from .models import Utilisateur, Conversation, Message, StatutUtilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('email', 'nom', 'est_actif')
    search_fields = ('email', 'nom')
    list_filter = ('est_actif',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_creation', 'date_mise_a_jour', 'get_participants')
    
    def get_participants(self, obj):
        return ", ".join([user.nom for user in obj.participants.all()])
    get_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('expediteur', 'conversation', 'contenu_court', 'date_envoi', 'est_lu')
    list_filter = ('est_lu', 'date_envoi')
    search_fields = ('contenu',)
    
    def contenu_court(self, obj):
        return obj.contenu[:50] + '...' if len(obj.contenu) > 50 else obj.contenu
    contenu_court.short_description = 'Contenu'

@admin.register(StatutUtilisateur)
class StatutUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'est_en_ligne', 'derniere_activite')
    list_filter = ('est_en_ligne',)