import os

from app import app
from models import db, Utilisateur, RoleUtilisateur

with app.app_context():

    if not Utilisateur.query.filter_by(email="user@test.com").first():
        user = Utilisateur(
            nom="Utilisateur Test",
            email="user@test.com",
            role=RoleUtilisateur.USER
        )
        user.set_password(os.environ["TEST_USER_PASSWORD"])
        db.session.add(user)

    if not Utilisateur.query.filter_by(email="tech@test.com").first():
        technicien = Utilisateur(
            nom="Technicien Test",
            email="tech@test.com",
            role=RoleUtilisateur.TECHNICIEN
        )
        technicien.set_password(os.environ["TEST_TECH_PASSWORD"])
        db.session.add(technicien)

    if not Utilisateur.query.filter_by(email="admin@test.com").first():
        admin = Utilisateur(
            nom="Administrateur",
            email="admin@test.com",
            role=RoleUtilisateur.ADMIN
        )
        admin.set_password(os.environ["TEST_ADMIN_PASSWORD"])
        db.session.add(admin)

    db.session.commit()

    print("Comptes de test créés avec succès.")