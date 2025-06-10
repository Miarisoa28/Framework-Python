-- Création de la base de données
CREATE DATABASE IF NOT EXISTS application_messagerie CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE application_messagerie;

-- Table des utilisateurs simplifiée
CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(128) NOT NULL,
    est_actif BOOLEAN DEFAULT TRUE
);

-- Table des conversations
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_mise_a_jour DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table pour associer les utilisateurs aux conversations
CREATE TABLE participants_conversation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    utilisateur_id INT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_conversation_utilisateur (conversation_id, utilisateur_id)
);

-- Table des messages
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    expediteur_id INT NOT NULL,
    contenu TEXT NOT NULL,
    date_envoi DATETIME DEFAULT CURRENT_TIMESTAMP,
    est_lu BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (expediteur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- Table des statuts de connexion des utilisateurs
CREATE TABLE statut_utilisateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL UNIQUE,
    est_en_ligne BOOLEAN DEFAULT FALSE,
    derniere_activite DATETIME,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- Ajout d'index pour optimiser les performances
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_expediteur ON messages(expediteur_id);
CREATE INDEX idx_participants_conversation_utilisateur ON participants_conversation(utilisateur_id);
CREATE INDEX idx_participants_conversation_conversation ON participants_conversation(conversation_id);