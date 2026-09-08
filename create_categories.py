from app import app
from models import db, Categorie

categories = [
    ("Réseau", "Problèmes de connexion, Wi-Fi, VPN ou réseau."),
    ("Logiciel", "Installation ou dysfonctionnement d'un logiciel."),
    ("Matériel", "Problèmes liés aux équipements informatiques."),
    ("Compte / Accès", "Problèmes de compte, mot de passe ou autorisation."),
    ("Autre", "Demandes ne correspondant pas aux autres catégories.")
]

with app.app_context():
    for nom, description in categories:
        categorie = Categorie.query.filter_by(nom=nom).first()

        if not categorie:
            db.session.add(
                Categorie(
                    nom=nom,
                    description=description
                )
            )

    db.session.commit()

    print("Catégories créées avec succès.")