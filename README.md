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

## Configuration sécurisée

Copier `.env.example` vers `.env` et remplacer toutes les valeurs `REMPLACER...` par des valeurs privées et uniques. Le fichier `.env` est ignoré par Git et Docker.

La variable `SECRET_KEY` est obligatoire pour lancer l'application Flask. Pour créer les comptes de démonstration avec `python create_users.py`, définir au préalable `TEST_USER_PASSWORD`, `TEST_TECH_PASSWORD` et `TEST_ADMIN_PASSWORD` avec des mots de passe uniques.

Ne pas publier de secrets Kubernetes, clés AWS, jetons ou bases de données. La configuration GitLab CI/CD et les manifestes Kubernetes ont été conservés ; les valeurs d'infrastructure doivent être vérifiées avant publication publique.
