# messagerie/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Utilisateur, Conversation, Message, StatutUtilisateur, GroupeDiscussion
from .forms import InscriptionUtilisateurForm, ConnexionForm, MessageForm
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad
import base64
import os


# Chemins vers les fichiers de clés
CHEMIN_CLE_PRIVEE = 'private.pem'
CHEMIN_CLE_PUBLIQUE = 'public.pem'

# Vérifie et génère les clés RSA si nécessaire
def verifier_cles_rsa():
    if not (os.path.exists(CHEMIN_CLE_PRIVEE) and os.path.exists(CHEMIN_CLE_PUBLIQUE)):
        generer_cles_rsa()

# Génère les clés RSA
def generer_cles_rsa():
    cle = RSA.generate(2048)
    cle_privee = cle.export_key()
    cle_publique = cle.publickey().export_key()

    with open(CHEMIN_CLE_PRIVEE, 'wb') as f:
        f.write(cle_privee)
    with open(CHEMIN_CLE_PUBLIQUE, 'wb') as f:
        f.write(cle_publique)

# Charge les clés RSA
def charger_cles_rsa():
    verifier_cles_rsa()
    with open(CHEMIN_CLE_PRIVEE, 'rb') as f:
        cle_privee = RSA.import_key(f.read())
    with open(CHEMIN_CLE_PUBLIQUE, 'rb') as f:
        cle_publique = RSA.import_key(f.read())
    return cle_privee, cle_publique

# Chiffrement RSA
def chiffrer_rsa(donnees_octets, cle_publique):
    if isinstance(cle_publique, str):
        cle_publique = RSA.import_key(cle_publique)
    chiffreur = PKCS1_OAEP.new(cle_publique)
    donnees_chiffrees = chiffreur.encrypt(donnees_octets)
    return base64.b64encode(donnees_chiffrees).decode()

# Déchiffrement RSA
def dechiffrer_rsa(donnees_chiffrees, cle_privee):
    if isinstance(cle_privee, str):
        cle_privee = RSA.import_key(cle_privee)
    dechiffreur = PKCS1_OAEP.new(cle_privee)
    donnees = base64.b64decode(donnees_chiffrees)
    return dechiffreur.decrypt(donnees)

# Chiffrement AES CBC
def chiffrer_aes(message, cle):
    vecteur_init = get_random_bytes(16)
    chiffreur = AES.new(cle, AES.MODE_CBC, vecteur_init)
    donnees_chiffrees = chiffreur.encrypt(pad(message.encode('utf-8'), AES.block_size))
    return base64.b64encode(vecteur_init).decode(), base64.b64encode(donnees_chiffrees).decode()

# Déchiffrement AES CBC
def dechiffrer_aes(vecteur_base64, donnees_base64, cle):
    vecteur_init = base64.b64decode(vecteur_base64)
    donnees_chiffrees = base64.b64decode(donnees_base64)
    dechiffreur = AES.new(cle, AES.MODE_CBC, vecteur_init)
    return unpad(dechiffreur.decrypt(donnees_chiffrees), AES.block_size).decode('utf-8')

verifier_cles_rsa()

# Fonction de vue d'inscription
def inscription(request):
    if request.method == 'POST':
        form = InscriptionUtilisateurForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            # Créer le statut pour le nouvel utilisateur
            StatutUtilisateur.objects.create(utilisateur=utilisateur)
            messages.success(request, 'Compte créé avec succès! Vous pouvez maintenant vous connecter.')
            return redirect('connexion')
    else:
        form = InscriptionUtilisateurForm()
    return render(request, 'messagerie/inscription.html', {'form': form})

# Fonction de vue de connexion
def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                # Mettre à jour le statut en ligne
                statut, created = StatutUtilisateur.objects.get_or_create(utilisateur=user)
                statut.est_en_ligne = True
                statut.derniere_activite = timezone.now()
                statut.save()
                return redirect('liste_conversations')
    else:
        form = ConnexionForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def deconnexion(request):
    # Mettre à jour le statut hors ligne
    statut = StatutUtilisateur.objects.get(utilisateur=request.user)
    statut.est_en_ligne = False
    statut.derniere_activite = timezone.now()
    statut.save()
    logout(request)
    return redirect('connexion')

@login_required
def liste_conversations(request):
    conversations = Conversation.objects.filter(participants=request.user)

    cle_privee, _ = charger_cles_rsa()

    # Préparer les données à afficher pour chaque conversation
    conversations_affichees = []
    for conversation in conversations:
        # Déterminer le nom à afficher
        if hasattr(conversation, 'groupe_discussion'):
            nom_affichage = conversation.groupe_discussion.nom
        else:
            autre = conversation.participants.exclude(id=request.user.id).first()
            nom_affichage = autre.nom if autre else "Conversation"

        # Récupérer le dernier message
        dernier_message = conversation.messages.last()
        if dernier_message:
            try:
                if hasattr(dernier_message, 'key') and dernier_message.key and hasattr(dernier_message, 'iv') and dernier_message.iv:
                    cle_chiffree = base64.b64decode(dernier_message.key.encode())
                    cle_aes = dechiffrer_rsa(cle_chiffree, cle_privee)
                    message_dechiffre = dechiffrer_aes(dernier_message.iv, dernier_message.contenu, cle_aes)
                    dernier_message.contenu_dechiffre = message_dechiffre
                else:
                    dernier_message.contenu_dechiffre = dernier_message.contenu
            except Exception as e:
                dernier_message.contenu_dechiffre = f"[Erreur de déchiffrement: {str(e)}]"
        else:
            dernier_message = None

        conversations_affichees.append({
            'id': conversation.id,
            'nom_affichage': nom_affichage,
            'dernier_message': dernier_message
        })

    utilisateurs = Utilisateur.objects.exclude(id=request.user.id)

    context = {
        'conversations_affichees': conversations_affichees,
        'utilisateurs': utilisateurs,
    }
    return render(request, 'messagerie/liste_conversations.html', context)


@login_required
def nouvelle_conversation(request, utilisateur_id):
    autre_utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    
    # Vérifier si une conversation existe déjà entre ces deux utilisateurs
    conversations_existantes = Conversation.objects.filter(participants=request.user).filter(participants=autre_utilisateur)
    
    if conversations_existantes.exists():
        conversation = conversations_existantes.first()
    else:
        # Créer une nouvelle conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, autre_utilisateur)
        conversation.save()
        
    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.user not in conversation.participants.all():
        messages.error(request, "Vous n'avez pas accès à cette conversation.")
        return redirect('liste_conversations')
    
    Message.objects.filter(
        conversation=conversation,
        est_lu=False
    ).exclude(expediteur=request.user).update(est_lu=True)
    
    messages_conversation = conversation.messages.all().order_by('date_envoi')
    
    if request.method == 'POST':
        # IMPORTANT : Pour les uploads de fichiers, utiliser request.FILES en plus de request.POST
        form = MessageForm(request.POST, request.FILES) 
        if form.is_valid():
            nouveau_message = form.save(commit=False)
            nouveau_message.expediteur = request.user
            nouveau_message.conversation = conversation
            
            # Récupérer le contenu textuel, le fichier ou le message vocal
            contenu_textuel = form.cleaned_data.get('contenu')
            fichier_envoye = form.cleaned_data.get('fichier')
            message_vocal_envoye = form.cleaned_data.get('message_vocal')

            if contenu_textuel:
                # Chiffrement du message texte
                key = get_random_bytes(16) 
                iv, encrypted_message = chiffrer_aes(contenu_textuel, key)
                
                _, public_key = charger_cles_rsa()
                encrypted_key = chiffrer_rsa(key, public_key)
                
                nouveau_message.contenu = encrypted_message
                nouveau_message.key = base64.b64encode(encrypted_key.encode()).decode()
                nouveau_message.iv = iv
                
            elif fichier_envoye:
                # Gérer l'upload et le chiffrement du fichier
                # Django gère l'enregistrement du fichier sur le disque via FileField
                # Nous chiffrons ensuite le contenu du fichier
                
                # Lire le contenu du fichier en octets
                file_content = fichier_envoye.read()
                
                key = get_random_bytes(16)
                # Chiffrer le contenu du fichier (octets)
                # Note: chiffrer_aes attend une chaîne, il faut l'adapter ou créer une nouvelle fonction
                # Pour simplifier, nous allons le décoder/encoder pour le chiffrement, mais attention aux binaires purs.
                # Une meilleure approche serait de chiffrer directement les octets.
                # Pour l'instant, faisons avec ce que tu as :
                
                # IMPORTANT : adapter chiffrer_aes pour prendre des octets directement
                # Pour l'exemple, je vais le convertir en base64 pour le chiffrement texte existant, 
                # mais idéalement, le chiffrement devrait être sur les octets bruts.
                # Ce serait mieux d'avoir une fonction chiffrement_aes_bytes(data_bytes, key)
                
                # Solution temporaire: encoder le contenu du fichier en base64 pour le chiffrer comme une chaîne
                base64_file_content = base64.b64encode(file_content).decode('utf-8')
                iv, encrypted_data_b64 = chiffrer_aes(base64_file_content, key)
                
                _, public_key = charger_cles_rsa()
                encrypted_key = chiffrer_rsa(key, public_key)
                
                nouveau_message.contenu = encrypted_data_b64 # Le contenu chiffré du fichier (en base64)
                nouveau_message.key = base64.b64encode(encrypted_key.encode()).decode()
                nouveau_message.iv = iv
                nouveau_message.fichier = fichier_envoye # Le FileField gérera l'enregistrement

            elif message_vocal_envoye:
                # Gérer l'upload et le chiffrement du message vocal
                audio_content = message_vocal_envoye.read()
                
                key = get_random_bytes(16)
                base64_audio_content = base64.b64encode(audio_content).decode('utf-8')
                iv, encrypted_audio_b64 = chiffrer_aes(base64_audio_content, key)
                
                _, public_key = charger_cles_rsa()
                encrypted_key = chiffrer_rsa(key, public_key)
                
                nouveau_message.contenu = encrypted_audio_b64 # Contenu chiffré de l'audio (en base64)
                nouveau_message.key = base64.b64encode(encrypted_key.encode()).decode()
                nouveau_message.iv = iv
                nouveau_message.message_vocal = message_vocal_envoye # Le FileField gérera l'enregistrement
            
            else:
                messages.error(request, "Veuillez saisir un message texte, sélectionner un fichier ou enregistrer un message vocal.")
                return redirect('conversation_detail', conversation_id=conversation.id)

            nouveau_message.est_lu = False
            nouveau_message.save()
            
            conversation.date_mise_a_jour = timezone.now()
            conversation.save()
            
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    if conversation.groupe_discussion:
        nom_a_afficher = conversation.groupe_discussion.nom
        autre_participant = None
    else:
        autre_participant = conversation.participants.exclude(id=request.user.id).first()
        nom_a_afficher = autre_participant.nom if autre_participant else "Conversation"

    # Déchiffrement des messages pour l'affichage
    try:
        private_key, _ = charger_cles_rsa()

        for msg in messages_conversation:
            try:
                # Déchiffrement du contenu chiffré (texte, fichier ou vocal)
                if hasattr(msg, 'key') and msg.key and hasattr(msg, 'iv') and msg.iv and msg.contenu:
                    encrypted_key = base64.b64decode(msg.key.encode())
                    aes_key = dechiffrer_rsa(encrypted_key, private_key)
                    
                    decrypted_data_b64 = dechiffrer_aes(msg.iv, msg.contenu, aes_key)
                    
                    # Si c'est un fichier ou un message vocal, le contenu déchiffré est en base64.
                    # Il faut le décoder pour l'utiliser.
                    # Pour un fichier ou vocal, tu ne le mettras pas directement dans contenu_dechiffre
                    # mais tu l'utiliserais dans le template pour générer un lien de téléchargement ou un lecteur.
                    
                    # Stocker le contenu déchiffré si c'est un message texte
                    if not msg.fichier and not msg.message_vocal:
                        msg.contenu_dechiffre = decrypted_data_b64
                    else:
                        # Si c'est un fichier ou vocal, le contenu_dechiffre contient le base64 du contenu binaire
                        msg.chiffred_data_base64 = decrypted_data_b64 
                else:
                    msg.contenu_dechiffre = msg.contenu # Si le message n'est pas chiffré (ex: anciens messages)
            except Exception as e:
                msg.contenu_dechiffre = f"[Erreur de déchiffrement: {str(e)}]"
    except Exception as e:
        for msg in messages_conversation:
            msg.contenu_dechiffre = f"[Erreur de déchiffrement globale: {str(e)}]"
    
    return render(request, 'messagerie/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages_conversation,
        'form': form,
        'autre_participant': autre_participant,
        'nom_a_afficher': nom_a_afficher,
    })


@login_required
def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.filter(est_actif=True).exclude(id=request.user.id)
    return render(request, 'messagerie/liste_utilisateurs.html', {'utilisateurs': utilisateurs})

@login_required
def creer_groupe(request):
    if request.method == 'POST':
        nom_groupe = request.POST.get('nom_groupe', '').strip()
        participant_ids = request.POST.getlist('participants')

        # Ajoute automatiquement l'ID du créateur à la liste des participants
        if str(request.user.id) not in participant_ids:
            participant_ids.append(str(request.user.id))

        if not nom_groupe:
            messages.error(request, "Veuillez saisir un nom pour le groupe.")
        elif not participant_ids:
            messages.error(request, "Veuillez sélectionner au moins un participant.")
        else:
            # Création de la conversation
            conversation = Conversation.objects.create()
            for user_id in participant_ids:
                try:
                    utilisateur = Utilisateur.objects.get(id=user_id)
                    conversation.participants.add(utilisateur)
                except Utilisateur.DoesNotExist:
                    pass
.
            # Création du groupe lié à la conversation
            groupe = GroupeDiscussion.objects.create(
                conversation=conversation,
                nom=nom_groupe,
            )
            groupe.membres.set(conversation.participants.all())

            messages.success(request, "Groupe de discussion créé avec succès !")
            return redirect('conversation_detail', conversation_id=conversation.id)

    utilisateurs = Utilisateur.objects.exclude(id=request.user.id)
    return render(request, 'messagerie/creer_groupe.html', {'utilisateurs': utilisateurs})
