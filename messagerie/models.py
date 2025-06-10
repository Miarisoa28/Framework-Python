# messagerie/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.contrib.auth import get_user_model # Pour obtenir le modèle User configuré

class UtilisateurManager(BaseUserManager):
    def create_user(self, email, nom, mot_de_passe=None):
        if not email:
            raise ValueError('L\'utilisateur doit avoir une adresse email')
        if not nom:
            raise ValueError('L\'utilisateur doit avoir un nom')
        
        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
        )
        user.set_password(mot_de_passe)
        user.save(using=self._db)
        return user

    # Django 5.x n'exige pas explicitement create_superuser dans BaseUserManager si vous ne le définissez pas manuellement
    # et que vous utilisez les commandes de gestion standard.
    # Cependant, si vous avez l'intention de le définir, voici une version simple:
    def create_superuser(self, email, nom, mot_de_passe=None):
        user = self.create_user(
            email=email,
            nom=nom,
            mot_de_passe=mot_de_passe,
        )
        # Ces attributs sont requis par Django pour les superutilisateurs
        user.is_admin = True
        user.is_staff = True # Utilisé par le site d'administration
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Utilisateur(AbstractBaseUser):
    email = models.EmailField(verbose_name='adresse email', max_length=191, unique=True)
    nom = models.CharField(max_length=150)
    est_actif = models.BooleanField(default=True)
    
    # Nouveau pour les superutilisateurs et l'accès admin
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False) # Pour Django 5.x, souvent associé à is_admin/is_staff

    objects = UtilisateurManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom'] # Champs requis lors de la création d'un utilisateur via createsuperuser

    def __str__(self):
        return self.nom # Plus lisible pour l'affichage

    # Méthodes requises pour les permissions d'administration si vous utilisez un CustomUser
    def has_perm(self, perm, obj=None):
        return self.is_admin # ou self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_admin # ou self.is_superuser

# Obtenez le modèle Utilisateur défini pour les relations
# Cela est nécessaire car 'Utilisateur' est un modèle de modèle de l'utilisateur personnalisé.
User = get_user_model() 

class Conversation(models.Model):
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    participants = models.ManyToManyField(User, related_name='conversations')
    
    def __str__(self):
        # Pour une conversation privée, afficher les noms des participants
        # Pour une conversation de groupe, le __str__ du GroupeDiscussion sera utilisé
        participant_names = ", ".join([p.nom for p in self.participants.all()])
        return f"Conversation ({self.id}) entre: {participant_names}"

class GroupeDiscussion(models.Model):
    # Une conversation peut être associée à un groupe de discussion
    # C'est ainsi que nous distinguons les conversations privées des conversations de groupe.
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='groupe_discussion' # Nom du related_name consistent avec votre code existant
    )
    nom = models.CharField(max_length=150, unique=True) # Le nom du groupe doit être unique
    # Les membres du groupe sont maintenant gérés via les participants de la conversation
    # A noter: Techniquement, les membres sont les participants de la conversation liée.
    # Ce champ 'membres' pourrait être redondant ou source de confusion si non géré correctement.
    # Pour la simplicité, on peut le garder pour des requêtes directes de groupe,
    # mais la source de vérité pour "qui est dans la conversation" devrait être Conversation.participants.
    # Si vous voulez l'utiliser pour la gestion d'un groupe distinct de la conversation elle-même,
    # alors il faut le conserver et s'assurer que les deux ManyToManyField sont synchronisés
    # lors de la création/modification d'un groupe.
    # Pour l'instant, je le laisse, mais je note l'ambiguïté.
    membres = models.ManyToManyField(User, related_name='groupes_auxquels_appartient') 
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class Message(models.Model):
    # Clé étrangère vers Conversation (qui peut être privée ou de groupe)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    
    # Contenu du message (texte, fichier, vocal)
    contenu = models.TextField(blank=True, null=True) # Contenu textuel chiffré
    fichier = models.FileField(upload_to='fichiers_messages/', blank=True, null=True)
    message_vocal = models.FileField(upload_to='messages_vocaux/', blank=True, null=True)
    
    # Champs pour le chiffrement AES
    # Ces champs devraient stocker les données binaires directement ou en base64 si nécessaire
    # Le 'chiffred_data_base64' était dans la vue précédemment, le mettre ici est plus cohérent
    # pour les fichiers et vocaux chiffrés.
    cle_chiffrement = models.BinaryField(blank=True, null=True) # Clé AES chiffrée avec la clé publique du destinataire
    iv = models.BinaryField(blank=True, null=True) # Vecteur d'initialisation AES
    chiffred_data_base64 = models.TextField(blank=True, null=True) # Pour les fichiers et vocaux chiffrés, si vous décidez de stocker la base64 du contenu chiffré.

    date_envoi = models.DateTimeField(auto_now_add=True)
    est_lu = models.BooleanField(default=False)

    # NOUVEAU CHAMP POUR LA SUPPRESSION
    supprime_par_expediteur = models.BooleanField(default=False)

    class Meta:
        ordering = ['date_envoi']
        
    def __str__(self):
        # Affiche un aperçu du message, en tenant compte de l'état de suppression
        if self.supprime_par_expediteur:
            return f"Message supprimé ({self.expediteur.nom} - {self.date_envoi.strftime('%H:%M')})"
        
        if self.contenu:
            return f"De {self.expediteur.nom}: {self.contenu[:50]}..."
        elif self.fichier:
            return f"De {self.expediteur.nom}: Fichier joint {self.fichier.name.split('/')[-1]}"
        elif self.message_vocal:
            return f"De {self.expediteur.nom}: Message vocal"
        return f"De {self.expediteur.nom}: Message vide"

    # Propriété pour le contenu à afficher dans le template, gérant la suppression
    @property
    def contenu_a_afficher(self):
        if self.supprime_par_expediteur:
            return "Ce message a été supprimé."
        # Si vous déchiffrez le contenu côté serveur et le stockez, utilisez-le ici
        # return self.contenu_dechiffre if self.contenu_dechiffre else self.contenu
        return self.contenu # Si le déchiffrement se fait côté client, renvoyez le contenu chiffré

class StatutUtilisateur(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statut')
    est_en_ligne = models.BooleanField(default=False)
    derniere_activite = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Statut de {self.utilisateur.nom}"