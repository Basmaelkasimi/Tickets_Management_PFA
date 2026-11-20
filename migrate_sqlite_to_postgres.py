import sqlite3
from app import app, db
from models import (
    Utilisateur,
    Categorie,
    Ticket,
    Commentaire,
    Notification,
    HistoriqueTicket,
    RoleUtilisateur,
    PrioriteTicket,
    StatutTicket,
)
from datetime import datetime


SQLITE_DB = "instance/tickets.db"


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


with app.app_context():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Migration SQLite -> PostgreSQL...")

    # -------------------------
    # 1. UTILISATEURS
    # -------------------------
    users = cursor.execute("SELECT * FROM utilisateur").fetchall()

    for row in users:
        existe = db.session.get(Utilisateur, row["id"])

        if existe:
            continue

        user = Utilisateur(
            id=row["id"],
            nom=row["nom"],
            email=row["email"],
            mot_de_passe_hash=row["mot_de_passe_hash"],
            role=RoleUtilisateur(row["role"]),
            date_creation=parse_datetime(row["date_creation"]),
        )

        db.session.add(user)

    db.session.commit()
    print(f"{len(users)} utilisateurs traités.")

    # -------------------------
    # 2. CATEGORIES
    # -------------------------
    categories = cursor.execute("SELECT * FROM categorie").fetchall()

    for row in categories:
        existe = db.session.get(Categorie, row["id"])

        if existe:
            continue

        categorie = Categorie(
            id=row["id"],
            nom=row["nom"],
            description=row["description"],
        )

        db.session.add(categorie)

    db.session.commit()
    print(f"{len(categories)} catégories traitées.")

    # -------------------------
    # 3. TICKETS
    # -------------------------
    tickets = cursor.execute("SELECT * FROM ticket").fetchall()

    for row in tickets:
        existe = db.session.get(Ticket, row["id"])

        if existe:
            continue

        ticket = Ticket(
            id=row["id"],
            titre=row["titre"],
            description=row["description"],
            localisation=row["localisation"],
            equipement=row["equipement"],
            priorite=PrioriteTicket(row["priorite"]),
            statut=StatutTicket(row["statut"]),
            date_creation=parse_datetime(row["date_creation"]),
            date_resolution=parse_datetime(row["date_resolution"]),
            demandeur_id=row["demandeur_id"],
            technicien_id=row["technicien_id"],
            categorie_id=row["categorie_id"],
        )

        db.session.add(ticket)

    db.session.commit()
    print(f"{len(tickets)} tickets traités.")

    # -------------------------
    # 4. COMMENTAIRES
    # -------------------------
    commentaires = cursor.execute("SELECT * FROM commentaire").fetchall()

    for row in commentaires:
        existe = db.session.get(Commentaire, row["id"])

        if existe:
            continue

        commentaire = Commentaire(
            id=row["id"],
            contenu=row["contenu"],
            date_creation=parse_datetime(row["date_creation"]),
            ticket_id=row["ticket_id"],
            utilisateur_id=row["utilisateur_id"],
        )

        db.session.add(commentaire)

    db.session.commit()
    print(f"{len(commentaires)} commentaires traités.")

    # -------------------------
    # 5. NOTIFICATIONS
    # -------------------------
    notifications = cursor.execute("SELECT * FROM notification").fetchall()

    for row in notifications:
        existe = db.session.get(Notification, row["id"])

        if existe:
            continue

        notification = Notification(
            id=row["id"],
            message=row["message"],
            lu=bool(row["lu"]),
            date_creation=parse_datetime(row["date_creation"]),
            utilisateur_id=row["utilisateur_id"],
            ticket_id=row["ticket_id"],
        )

        db.session.add(notification)

    db.session.commit()
    print(f"{len(notifications)} notifications traitées.")

    # -------------------------
    # 6. HISTORIQUE
    # -------------------------
    historiques = cursor.execute("SELECT * FROM historique_ticket").fetchall()

    for row in historiques:
        existe = db.session.get(HistoriqueTicket, row["id"])

        if existe:
            continue

        historique = HistoriqueTicket(
            id=row["id"],
            action=row["action"],
            date_action=parse_datetime(row["date_action"]),
            ticket_id=row["ticket_id"],
            utilisateur_id=row["utilisateur_id"],
        )

        db.session.add(historique)

    db.session.commit()

    print(f"{len(historiques)} historiques traités.")
    print("Migration terminée avec succès.")

    conn.close()