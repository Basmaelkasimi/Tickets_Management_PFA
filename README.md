# Ticket Management Helpdesk

Application web de gestion des tickets de support développée avec Flask.

## Présentation

Ticket Management Helpdesk permet de centraliser et de suivre les demandes
de support entre les utilisateurs, les administrateurs et les techniciens.

L'application propose trois espaces distincts :

- Utilisateur
- Administrateur
- Technicien

## Fonctionnalités

### Utilisateur

- Authentification
- Création de tickets
- Consultation et suivi des tickets
- Ajout de commentaires
- Consultation de l'historique
- Réception de notifications
- Gestion du profil

### Administrateur

- Tableau de bord
- Consultation de tous les tickets
- Affectation des tickets aux techniciens
- Gestion des catégories
- Consultation des utilisateurs
- Consultation des techniciens
- Historique des actions
- Notifications
- Gestion du profil

### Technicien

- Consultation des tickets assignés
- Modification du statut des tickets
- Ajout de commentaires
- Suivi des interventions
- Historique
- Notifications

## Cycle de traitement d'un ticket

```text
NOUVEAU
   ↓
ASSIGNE
   ↓
EN_COURS
   ↓
EN_ATTENTE
   ↓
RESOLU
   ↓
FERME