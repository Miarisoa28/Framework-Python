# messagerie/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    
    # Conversations
    path('', views.liste_conversations, name='liste_conversations'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('nouvelle-conversation/<int:utilisateur_id>/', views.nouvelle_conversation, name='nouvelle_conversation'),

    # Utilisateurs
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('creer_groupe/', views.creer_groupe, name='creer_groupe'),

    path('message/<int:message_id>/delete/', views.supprimer_message, name='supprimer_message'),
]