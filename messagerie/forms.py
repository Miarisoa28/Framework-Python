# messagerie/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Utilisateur, Message

class InscriptionUtilisateurForm(UserCreationForm):
    email = forms.EmailField(max_length=191, required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    nom = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}))
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}))
    password2 = forms.CharField(label='Confirmation du mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmation du mot de passe'}))

    class Meta:
        model = Utilisateur
        fields = ('email', 'nom', 'password1', 'password2')

class ConnexionForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}))

class MessageForm(forms.ModelForm):
    # Rendre le contenu du message textuel optionnel si un fichier est envoyé
    contenu = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    fichier = forms.FileField(required=False)
    message_vocal = forms.FileField(required=False) # Ajout pour le message vocal

    class Meta:
        model = Message
        fields = ['contenu', 'fichier', 'message_vocal']
        # Assure-toi que les champs sont bien inclus dans les fields si tu utilises all() ou spécifie-les