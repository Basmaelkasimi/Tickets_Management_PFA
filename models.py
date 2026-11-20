from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class RoleUtilisateur(Enum):
    USER = "USER"
    TECHNICIEN = "TECHNICIEN"
    ADMIN = "ADMIN"


class PrioriteTicket(Enum):
    FAIBLE = "FAIBLE"
    MOYENNE = "MOYENNE"
    HAUTE = "HAUTE"
    CRITIQUE = "CRITIQUE"


class StatutTicket(Enum):
    NOUVEAU = "NOUVEAU"
    ASSIGNE = "ASSIGNE"
    EN_COURS = "EN_COURS"
    EN_ATTENTE = "EN_ATTENTE"
    RESOLU = "RESOLU"
    FERME = "FERME"


class Utilisateur(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleUtilisateur), nullable=False)

    service = db.Column(db.String(100), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def check_password(self, mot_de_passe):
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

class Categorie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    priorite = db.Column(
        db.Enum(PrioriteTicket),
        default=PrioriteTicket.MOYENNE,
        nullable=False
    )

    statut = db.Column(
        db.Enum(StatutTicket),
        default=StatutTicket.NOUVEAU,
        nullable=False
    )

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_resolution = db.Column(db.DateTime, nullable=True)
    solution_resolution = db.Column(db.Text, nullable=True)

    demandeur_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id"),
        nullable=False
    )

    technicien_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id"),
        nullable=True
    )

    categorie_id = db.Column(
        db.Integer,
        db.ForeignKey("categorie.id"),
        nullable=False
    )


    autre_categorie = db.Column(
    db.String(150),
    nullable=True
)

    # Relations
    demandeur = db.relationship(
        "Utilisateur",
        foreign_keys=[demandeur_id],
        backref="tickets_crees"
    )

    technicien = db.relationship(
        "Utilisateur",
        foreign_keys=[technicien_id],
        backref="tickets_assignes"
    )

    categorie = db.relationship(
        "Categorie",
        backref="tickets"
    )

    localisation = db.Column(db.String(150), nullable=True)
    equipement = db.Column(db.String(150), nullable=True)
    

class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id"),
        nullable=False
    )

    utilisateur_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id"),
        nullable=False
    )

    ticket = db.relationship(
        "Ticket",
        backref=db.backref(
            "commentaires",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    auteur = db.relationship(
        "Utilisateur",
        backref="commentaires"
    )


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    lu = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateur_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id"),
        nullable=False
    )

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id"),
        nullable=True
    )

    utilisateur = db.relationship(
        "Utilisateur",
        backref="notifications"
    )

    ticket = db.relationship(
        "Ticket",
        backref="notifications"
    )

class HistoriqueTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    action = db.Column(
        db.String(255),
        nullable=False
    )

    date_action = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("ticket.id"),
        nullable=False
    )

    utilisateur_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id"),
        nullable=True
    )

    ticket = db.relationship(
        "Ticket",
        backref="historique"
    )

    utilisateur = db.relationship(
        "Utilisateur"
    )