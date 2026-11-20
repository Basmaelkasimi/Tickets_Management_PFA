import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from dotenv import load_dotenv
from models import (
    db,
    Utilisateur,
    RoleUtilisateur,
    Ticket,
    Categorie,
    Commentaire,
    HistoriqueTicket,
    Notification,
    PrioriteTicket,
    StatutTicket
)
load_dotenv()

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///tickets.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]



# Configuration email
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Utilisateur, int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and utilisateur.check_password(mot_de_passe):
            login_user(utilisateur)

            if utilisateur.role == RoleUtilisateur.USER:
                return redirect(url_for("dashboard_user"))

            elif utilisateur.role == RoleUtilisateur.TECHNICIEN:
                return redirect(url_for("dashboard_technicien"))

            elif utilisateur.role == RoleUtilisateur.ADMIN:
                return redirect(url_for("dashboard_admin"))

        flash("Email ou mot de passe incorrect.")

    return render_template("login.html")


@app.route("/user/dashboard")
@login_required
def dashboard_user():

    if current_user.role != RoleUtilisateur.USER:
        return redirect(url_for("login"))

    # Tous les tickets de l'utilisateur
    all_tickets = (
        Ticket.query
        .filter_by(demandeur_id=current_user.id)
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # Statistiques globales
    total_tickets = len(all_tickets)

    tickets_ouverts = sum(
        1 for ticket in all_tickets
        if ticket.statut in [
            StatutTicket.NOUVEAU,
            StatutTicket.ASSIGNE,
            StatutTicket.EN_COURS,
            StatutTicket.EN_ATTENTE
        ]
    )


    tickets_en_cours = sum(
    1 for ticket in all_tickets
    if ticket.statut == StatutTicket.EN_COURS
)
    tickets_attente = sum(
        1 for ticket in all_tickets
        if ticket.statut == StatutTicket.EN_ATTENTE
    )

    tickets_resolus = sum(
        1 for ticket in all_tickets
        if ticket.statut in [
            StatutTicket.RESOLU,
            StatutTicket.FERME
        ]
    )

    # Récupérer les paramètres de recherche / filtre
    recherche = request.args.get("q", "").strip()
    statut_filtre = request.args.get("statut", "").strip()

    # Requête filtrée pour la liste affichée
    query = Ticket.query.filter_by(
        demandeur_id=current_user.id
    )

    # Recherche par titre ou numéro du ticket
    if recherche:
        if recherche.isdigit():
            query = query.filter(
                db.or_(
                    Ticket.titre.ilike(f"%{recherche}%"),
                    Ticket.id == int(recherche)
                )
            )
        else:
            query = query.filter(
                Ticket.titre.ilike(f"%{recherche}%")
            )

    # Filtre par statut
    if statut_filtre:
        try:
            query = query.filter(
                Ticket.statut == StatutTicket[statut_filtre]
            )
        except KeyError:
            pass

    # Tickets à afficher
    tickets = (
        query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # Ticket sélectionné
    ticket_id = request.args.get("ticket", type=int)

    selected_ticket = None

    if ticket_id:
        selected_ticket = Ticket.query.filter_by(
            id=ticket_id,
            demandeur_id=current_user.id
        ).first()

    # Si aucun ticket sélectionné, afficher le premier résultat
    if selected_ticket is None and tickets:
        selected_ticket = tickets[0]

    return render_template(
        "user/dashboard.html",
        tickets=tickets,
        total_tickets=total_tickets,
        tickets_ouverts=tickets_ouverts,
        tickets_en_cours=tickets_en_cours,
        tickets_attente=tickets_attente,
        tickets_resolus=tickets_resolus,
        selected_ticket=selected_ticket
    )


@app.route("/user/tickets")
@login_required
def tickets_user():

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    recherche = request.args.get("q", "").strip()
    statut_filtre = request.args.get("statut", "").strip()

    query = Ticket.query.filter_by(
        demandeur_id=current_user.id
    )

    # -------------------------
    # RECHERCHE
    # -------------------------
    if recherche:

        recherche_id = (
            recherche.upper()
            .replace("#", "")
            .replace("TK-", "")
            .strip()
        )

        if recherche_id.isdigit():

            query = query.filter(
                db.or_(
                    Ticket.id == int(recherche_id),
                    Ticket.titre.ilike(f"%{recherche}%")
                )
            )

        else:

            query = query.filter(
                Ticket.titre.ilike(f"%{recherche}%")
            )

    # -------------------------
    # FILTRE STATUT
    # -------------------------
    if statut_filtre:

        try:
            query = query.filter(
                Ticket.statut == StatutTicket[statut_filtre]
            )

        except KeyError:
            pass

    # -------------------------
    # LISTE DES TICKETS
    # -------------------------
    tickets = (
        query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # -------------------------
    # CATEGORIES POUR MODIFICATION
    # -------------------------
    categories = (
        Categorie.query
        .order_by(Categorie.nom.asc())
        .all()
    )

    return render_template(
        "user/tickets.html",
        tickets=tickets,
        categories=categories,
        StatutTicket=StatutTicket
    )


@app.route("/user/ticket/<int:ticket_id>/modifier", methods=["POST"])
@login_required
def modifier_ticket_user(ticket_id):

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.demandeur_id != current_user.id:
        flash("Vous ne pouvez pas modifier ce ticket.")
        return redirect(url_for("tickets_user"))

    if ticket.statut != StatutTicket.NOUVEAU:
        flash("Ce ticket ne peut plus être modifié.")
        return redirect(url_for("tickets_user"))

    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()
    priorite = request.form.get("priorite", "").strip()
    categorie_id = request.form.get("categorie_id", type=int)
    autre_categorie = request.form.get("autre_categorie", "").strip()
    localisation = request.form.get("localisation", "").strip()
    equipement = request.form.get("equipement", "").strip()

    if not titre or not description or not priorite or not categorie_id:
        flash("Veuillez remplir les champs obligatoires.")
        return redirect(url_for("tickets_user"))

    try:
        priorite_enum = PrioriteTicket[priorite]
    except KeyError:
        flash("Priorité invalide.")
        return redirect(url_for("tickets_user"))

    categorie = Categorie.query.get(categorie_id)

    if not categorie:
        flash("Catégorie invalide.")
        return redirect(url_for("tickets_user"))

    # Gestion de la catégorie "Autre"
    if categorie.nom.strip().lower() == "autre":

      if not autre_categorie:
        flash("Veuillez préciser la catégorie.")
        return redirect(url_for("tickets_user"))

    else:
       autre_categorie = None

    ticket.titre = titre
    ticket.description = description
    ticket.priorite = priorite_enum
    ticket.categorie_id = categorie_id
    ticket.autre_categorie = autre_categorie
    ticket.localisation = localisation
    ticket.equipement = equipement

    historique = HistoriqueTicket(
        action="Ticket modifié par l'utilisateur",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)
    db.session.commit()

    flash("Ticket modifié avec succès.")

    return redirect(url_for("tickets_user"))

@app.route("/user/ticket/<int:ticket_id>/supprimer", methods=["POST"])
@login_required
def supprimer_ticket_user(ticket_id):

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.demandeur_id != current_user.id:
        flash("Vous ne pouvez pas supprimer ce ticket.")
        return redirect(url_for("tickets_user"))

    if ticket.statut != StatutTicket.NOUVEAU:
        flash("Seuls les nouveaux tickets peuvent être supprimés.")
        return redirect(url_for("tickets_user"))

    # Supprimer les données liées avant le ticket
    HistoriqueTicket.query.filter_by(ticket_id=ticket.id).delete()
    Notification.query.filter_by(ticket_id=ticket.id).delete()
    Commentaire.query.filter_by(ticket_id=ticket.id).delete()

    db.session.delete(ticket)
    db.session.commit()

    flash("Ticket supprimé avec succès.")

    return redirect(url_for("tickets_user"))




import re


def suggerer_solutions(ticket_actuel, limite=3):
    """
    Recherche des anciens tickets réellement similaires
    en se basant sur les mots-clés importants du ticket actuel.
    """

    import re
    import unicodedata

    # ==========================================
    # 1. NORMALISER LE TEXTE
    # ==========================================

    def normaliser(texte):

        if not texte:
            return ""

        texte = texte.lower()

        # Enlever les accents
        texte = unicodedata.normalize("NFD", texte)

        texte = "".join(
            caractere
            for caractere in texte
            if unicodedata.category(caractere) != "Mn"
        )

        # Garder lettres et chiffres
        texte = re.sub(
            r"[^a-z0-9\s-]",
            " ",
            texte
        )

        return texte


    # ==========================================
    # 2. MOTS À IGNORER
    # ==========================================

    mots_vides = {
        # Français
        "avec", "dans", "pour", "une", "des",
        "les", "que", "qui", "sur", "pas",
        "plus", "mon", "mes", "son", "ses",
        "aux", "est", "sont", "par", "du",
        "de", "la", "le", "un", "au", "en",
        "et", "ou", "ce", "cette", "ces",
        "ne", "se", "je", "nous", "vous",
        "il", "elle",

        # Mots trop génériques pour un ticket
        "probleme",
        "incident",
        "ticket",
        "erreur",
        "test",
        "fonctionne",
        "fonctionner",
        "impossible",
        "besoin",
        "utilisateur",
        "ordinateur",
        "poste",
        "bureau"
    }


    # ==========================================
    # 3. EXTRACTION DES MOTS-CLÉS
    # ==========================================

    def extraire_mots(texte):

        texte = normaliser(texte)

        mots = re.findall(
            r"\b[a-z0-9-]{3,}\b",
            texte
        )

        return {
            mot
            for mot in mots
            if mot not in mots_vides
        }


    # ==========================================
    # 4. TEXTE DU TICKET ACTUEL
    # ==========================================

    texte_actuel = (
        f"{ticket_actuel.titre or ''} "
        f"{ticket_actuel.description or ''} "
        f"{ticket_actuel.equipement or ''}"
    )

    mots_actuels = extraire_mots(
        texte_actuel
    )

    # Aucun vrai mot-clé
    if not mots_actuels:
        return []


    # ==========================================
    # 5. ANCIENS TICKETS RÉSOLUS
    # ==========================================

    anciens_tickets = (
        Ticket.query
        .filter(
            Ticket.id != ticket_actuel.id,

            Ticket.statut.in_([
                StatutTicket.RESOLU,
                StatutTicket.FERME
            ]),

            Ticket.solution_resolution.isnot(None),

            Ticket.solution_resolution != ""
        )
        .all()
    )


    propositions = []


    # ==========================================
    # 6. COMPARAISON
    # ==========================================

    for ancien in anciens_tickets:

        texte_ancien = (
            f"{ancien.titre or ''} "
            f"{ancien.description or ''} "
            f"{ancien.equipement or ''}"
        )

        mots_ancien = extraire_mots(
            texte_ancien
        )

        mots_communs = (
            mots_actuels
            .intersection(mots_ancien)
        )

        # --------------------------------------
        # IMPORTANT :
        # Au moins un vrai mot-clé commun
        # --------------------------------------

        if not mots_communs:
            continue


        # ======================================
        # SCORE DE SIMILARITÉ
        # ======================================

        score = 0

        # Chaque vrai mot commun = 3 points
        score += len(mots_communs) * 3


        # Même catégorie = petit bonus seulement
        if (
            ticket_actuel.categorie_id
            and ancien.categorie_id
            and ticket_actuel.categorie_id
            == ancien.categorie_id
        ):
            score += 1


        # Même équipement = bonus important
        if (
            ticket_actuel.equipement
            and ancien.equipement
            and normaliser(ticket_actuel.equipement)
            == normaliser(ancien.equipement)
        ):
            score += 3


        # ======================================
        # TAUX DE SIMILARITÉ
        # ======================================

        similarite = (
            len(mots_communs)
            / len(mots_actuels)
        )

        # On exige au moins 20 %
        # des mots-clés du ticket actuel
        if similarite < 0.20:
            continue


        propositions.append({

            "ticket_id":
                ancien.id,

            "solution":
                ancien.solution_resolution,

            "score":
                score,

            "similarite":
                round(
                    similarite * 100
                ),

            "mots_communs":
                sorted(mots_communs)
        })


    # ==========================================
    # 7. CLASSER LES MEILLEURES SOLUTIONS
    # ==========================================

    propositions.sort(
        key=lambda proposition: (
            proposition["score"],
            proposition["similarite"]
        ),
        reverse=True
    )


    # ==========================================
    # 8. SUPPRIMER LES DOUBLONS
    # ==========================================

    solutions_uniques = []

    solutions_vues = set()


    for proposition in propositions:

        solution_normalisee = normaliser(
            proposition["solution"]
        )

        if solution_normalisee in solutions_vues:
            continue

        solutions_vues.add(
            solution_normalisee
        )

        solutions_uniques.append(
            proposition
        )

        if len(solutions_uniques) >= limite:
            break


    return solutions_uniques
@app.route("/technicien/dashboard")
@login_required
def dashboard_technicien():

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # ==========================================
    # TOUS LES TICKETS DU TECHNICIEN
    # ==========================================

    all_tickets = (
        Ticket.query
        .filter_by(technicien_id=current_user.id)
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # ==========================================
    # STATISTIQUES
    # ==========================================

    total_tickets = len(all_tickets)

    tickets_en_cours = sum(
        1 for ticket in all_tickets
        if ticket.statut == StatutTicket.EN_COURS
    )

    tickets_attente = sum(
        1 for ticket in all_tickets
        if ticket.statut == StatutTicket.EN_ATTENTE
    )

    tickets_resolus = sum(
        1 for ticket in all_tickets
        if ticket.statut in [
            StatutTicket.RESOLU,
            StatutTicket.FERME
        ]
    )

    # ==========================================
    # RECHERCHE
    # ==========================================

    recherche = request.args.get("q", "").strip()

    # ==========================================
    # FILTRE STATUT
    # ==========================================

    statut_filtre = request.args.get("statut", "").strip()

    query = Ticket.query.filter_by(
        technicien_id=current_user.id
    )

    # Recherche par titre ou numéro
    if recherche:

        if recherche.isdigit():

            query = query.filter(
                db.or_(
                    Ticket.titre.ilike(f"%{recherche}%"),
                    Ticket.id == int(recherche)
                )
            )

        else:

            query = query.filter(
                Ticket.titre.ilike(f"%{recherche}%")
            )

    # Filtre statut
    if statut_filtre:

        try:

            query = query.filter(
                Ticket.statut == StatutTicket[statut_filtre]
            )

        except KeyError:
            pass

    tickets = (
        query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # ==========================================
    # TICKET SELECTIONNE
    # ==========================================

    ticket_id = request.args.get(
        "ticket",
        type=int
    )

    selected_ticket = None

    if ticket_id:

        selected_ticket = Ticket.query.filter_by(
            id=ticket_id,
            technicien_id=current_user.id
        ).first()

    # Premier ticket par défaut
    if selected_ticket is None and tickets:

        selected_ticket = tickets[0]

      # ==========================================
    # MODE TRAITEMENT
    # ==========================================

    mode_traitement = (
        request.args.get("mode") == "traitement"
        and selected_ticket is not None
    )

    # ==========================================
    # SUGGESTIONS DE SOLUTIONS
    # ==========================================

    solutions_suggerees = []

    if mode_traitement and selected_ticket:
        solutions_suggerees = suggerer_solutions(
            selected_ticket,
            limite=3
        )

    # ==========================================
    # TEMPLATE
    # ==========================================

    return render_template(
        "technicien/dashboard.html",

        tickets=tickets,

        total_tickets=total_tickets,

        tickets_en_cours=tickets_en_cours,

        tickets_attente=tickets_attente,

        tickets_resolus=tickets_resolus,

        selected_ticket=selected_ticket,

        mode_traitement=mode_traitement,

        solutions_suggerees=solutions_suggerees
    )

@app.route("/technicien/historique")
@login_required
def historique_technicien():

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    recherche = request.args.get("q", "").strip()
    categorie_id = request.args.get("categorie", type=int)

    # Historique = anciens incidents déjà résolus ou fermés
    query = Ticket.query.filter(
    Ticket.technicien_id == current_user.id,
    Ticket.statut.in_([
        StatutTicket.RESOLU,
        StatutTicket.FERME
    ])
)

    # Recherche par titre, description ou numéro
    if recherche:

        if recherche.isdigit():

            query = query.filter(
                db.or_(
                    Ticket.id == int(recherche),
                    Ticket.titre.ilike(f"%{recherche}%"),
                    Ticket.description.ilike(f"%{recherche}%")
                )
            )

        else:

            query = query.filter(
                db.or_(
                    Ticket.titre.ilike(f"%{recherche}%"),
                    Ticket.description.ilike(f"%{recherche}%")
                )
            )

    # Filtre catégorie
    if categorie_id:
        query = query.filter(
            Ticket.categorie_id == categorie_id
        )

    incidents = (
        query
        .order_by(Ticket.date_resolution.desc())
        .all()
    )

    categories = (
        Categorie.query
        .order_by(Categorie.nom.asc())
        .all()
    )

    return render_template(
        "technicien/historique.html",
        incidents=incidents,
        categories=categories
    )

@app.route("/technicien/notifications")
@login_required
def notifications_technicien():

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    notifications = (
        Notification.query
        .filter_by(utilisateur_id=current_user.id)
        .order_by(Notification.date_creation.desc())
        .all()
    )

    return render_template(
        "technicien/notifications.html",
        notifications=notifications
    )

@app.route("/technicien/profil", methods=["GET", "POST"])
@login_required
def profil_technicien():

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        nouveau_mot_de_passe = request.form.get(
            "nouveau_mot_de_passe", ""
        ).strip()

        if not nom or not email:
            flash("Le nom et l'email sont obligatoires.")
            return redirect(url_for("profil_technicien"))

        utilisateur_existant = (
            Utilisateur.query
            .filter(
                Utilisateur.email == email,
                Utilisateur.id != current_user.id
            )
            .first()
        )

        if utilisateur_existant:
            flash("Cette adresse email est déjà utilisée.")
            return redirect(url_for("profil_technicien"))

        current_user.nom = nom
        current_user.email = email

        if nouveau_mot_de_passe:
            current_user.set_password(nouveau_mot_de_passe)

        db.session.commit()

        flash("Profil mis à jour avec succès.")

        return redirect(url_for("profil_technicien"))

    return render_template(
        "technicien/profil.html"
    )

@app.route("/technicien/tickets")
@login_required
def tickets_technicien():

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    recherche = request.args.get("q", "").strip()
    statut_filtre = request.args.get("statut", "").strip()

    query = Ticket.query.filter_by(
        technicien_id=current_user.id
    )

    if recherche:
        if recherche.isdigit():
            query = query.filter(
                db.or_(
                    Ticket.titre.ilike(f"%{recherche}%"),
                    Ticket.id == int(recherche)
                )
            )
        else:
            query = query.filter(
                Ticket.titre.ilike(f"%{recherche}%")
            )

    if statut_filtre:
        try:
            query = query.filter(
                Ticket.statut == StatutTicket[statut_filtre]
            )
        except KeyError:
            pass

    tickets = (
        query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    return render_template(
        "technicien/tickets.html",
        tickets=tickets
    )

@app.route("/admin/ticket/<int:ticket_id>/assigner", methods=["POST"])
@login_required
def assigner_ticket(ticket_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(ticket_id)

    technicien_id = request.form.get("technicien_id")

    if not technicien_id:
        flash("Veuillez sélectionner un technicien.")
        return redirect(url_for("dashboard_admin"))

    technicien = Utilisateur.query.filter_by(
        id=int(technicien_id),
        role=RoleUtilisateur.TECHNICIEN
    ).first()

    if not technicien:
        flash("Technicien invalide.")
        return redirect(url_for("dashboard_admin"))

    # Assigner le ticket
    ticket.technicien_id = technicien.id
    ticket.statut = StatutTicket.ASSIGNE

    # Historique
    historique = HistoriqueTicket(
        action=f"Ticket assigné à {technicien.nom}",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

    # Notification interne au technicien
    notification = Notification(
        message=f"Le ticket #{ticket.id} vous a été assigné.",
        utilisateur_id=technicien.id,
        ticket_id=ticket.id
    )

    db.session.add(notification)

    # Sauvegarder l'assignation
    db.session.commit()

    # ==========================================
    # EMAIL AU TECHNICIEN SI TICKET CRITIQUE
    # ==========================================

    if ticket.priorite == PrioriteTicket.CRITIQUE and technicien.email:

        msg = Message(
            subject=f"URGENT - Ticket critique #{ticket.id} assigné",
            recipients=[technicien.email],
            body=f"""
Bonjour {technicien.nom},

Un ticket CRITIQUE vient de vous être assigné.

Ticket : #{ticket.id}
Titre : {ticket.titre}
Priorité : CRITIQUE
Catégorie : {ticket.categorie.nom if ticket.categorie else "Non renseignée"}
Localisation : {ticket.localisation}
Équipement : {ticket.equipement or "Non renseigné"}

Description :
{ticket.description}

Veuillez consulter la plateforme Ticket Management et prendre en charge ce ticket.

Cordialement,
Ticket Management
"""
        )

        try:
            mail.send(msg)

        except Exception as e:
            app.logger.error(
                "Erreur lors de l'envoi de l'email critique au technicien #%s : %s",
                ticket.id,
                e
            )

    flash("Ticket assigné avec succès.")

    return redirect(url_for("dashboard_admin"))


@app.route("/technicien/ticket/<int:ticket_id>/commentaire", methods=["POST"])
@login_required
def ajouter_commentaire_technicien(ticket_id):

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.filter_by(
        id=ticket_id,
        technicien_id=current_user.id
    ).first_or_404()

    contenu = request.form.get("contenu", "").strip()

    if not contenu:
        flash("Le commentaire ne peut pas être vide.")
        return redirect(
            url_for(
                "dashboard_technicien",
                ticket=ticket.id
            )
        )

    commentaire = Commentaire(
        contenu=contenu,
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(commentaire)

    historique = HistoriqueTicket(
        action="Commentaire ajouté par le technicien",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

    notification = Notification(
        message=f"Le technicien a répondu à votre ticket #{ticket.id}.",
        utilisateur_id=ticket.demandeur_id,
        ticket_id=ticket.id
    )

    db.session.add(notification)

    db.session.commit()

    flash("Commentaire ajouté avec succès.")

    return redirect(
        url_for(
            "dashboard_technicien",
            ticket=ticket.id
        )
    )
@app.route("/admin/dashboard")
@login_required
def dashboard_admin():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # =========================
    # FILTRE PAR CALENDRIER
    # =========================

    date_debut = request.args.get("date_debut")
    date_fin = request.args.get("date_fin")

    query = Ticket.query

    if date_debut:
        query = query.filter(
            Ticket.date_creation >= datetime.strptime(
                date_debut,
                "%Y-%m-%d"
            )
        )

    if date_fin:
        date_fin_obj = datetime.strptime(
            date_fin,
            "%Y-%m-%d"
        ) + timedelta(days=1)

        query = query.filter(
            Ticket.date_creation < date_fin_obj
        )

    # =========================
    # TICKETS FILTRÉS
    # =========================

    tickets = (
        query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    techniciens = (
        Utilisateur.query
        .filter_by(role=RoleUtilisateur.TECHNICIEN)
        .order_by(Utilisateur.nom)
        .all()
    )

    # =========================
    # KPI
    # =========================

    total_tickets = len(tickets)

    tickets_nouveaux = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.NOUVEAU
    )

    tickets_en_cours = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.EN_COURS
    )

    tickets_resolus = sum(
        1 for ticket in tickets
        if ticket.statut in [
            StatutTicket.RESOLU,
            StatutTicket.FERME
        ]
    )

    tickets_recents = tickets[:5]

    return render_template(
        "admin/dashboard.html",
        tickets=tickets,
        techniciens=techniciens,
        total_tickets=total_tickets,
        tickets_nouveaux=tickets_nouveaux,
        tickets_en_cours=tickets_en_cours,
        tickets_resolus=tickets_resolus,
        tickets_recents=tickets_recents
    )


@app.route("/admin/tickets")
@login_required
def admin_tickets():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Récupération des filtres
    recherche = request.args.get("q", "").strip()
    statut = request.args.get("statut", "").strip()
    date_debut = request.args.get("date_debut", "").strip()
    date_fin = request.args.get("date_fin", "").strip()

    query = Ticket.query

    # Recherche par titre
    # Recherche par titre ou numéro du ticket
  # Recherche par titre ou numéro du ticket
    if recherche:

        recherche_id = (
        recherche.upper()
        .replace("#", "")
        .replace("TK-", "")
        .replace("TICKET", "")
        .strip()
    )

        if recherche_id.isdigit():

            query = query.filter(
            db.or_(
                Ticket.id == int(recherche_id),
                Ticket.titre.ilike(f"%{recherche}%")
            )
        )

        else:

             query = query.filter(
            Ticket.titre.ilike(f"%{recherche}%")
        )

    # Filtre par statut
    if statut:
        try:
            statut_enum = StatutTicket[statut]

            query = query.filter(
                Ticket.statut == statut_enum
            )

        except KeyError:
            pass

    # Filtre date de début
    if date_debut:
        try:
            debut = datetime.strptime(
                date_debut,
                "%Y-%m-%d"
            )

            query = query.filter(
                Ticket.date_creation >= debut
            )

        except ValueError:
            pass

    # Filtre date de fin
    if date_fin:
        try:
            fin = (
                datetime.strptime(
                    date_fin,
                    "%Y-%m-%d"
                )
                + timedelta(days=1)
            )

            query = query.filter(
                Ticket.date_creation < fin
            )

        except ValueError:
            pass

    # Résultat final
    tickets = (
        query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # Liste des techniciens
    techniciens = (
        Utilisateur.query
        .filter_by(role=RoleUtilisateur.TECHNICIEN)
        .order_by(Utilisateur.nom)
        .all()
    )

    return render_template(
        "admin/tickets.html",
        tickets=tickets,
        techniciens=techniciens,
        recherche=recherche,
        statut_selectionne=statut,
        statuts=StatutTicket,
        date_debut=date_debut,
        date_fin=date_fin
    )

@app.route("/admin/statistiques")
@login_required
def admin_statistiques():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # =========================
    # TOUS LES TICKETS
    # =========================
    tickets = Ticket.query.all()

    total_tickets = len(tickets)

    # =========================
    # STATISTIQUES PAR STATUT
    # =========================
    tickets_nouveaux = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.NOUVEAU
    )

    tickets_assignes = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.ASSIGNE
    )

    tickets_en_cours = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.EN_COURS
    )

    tickets_en_attente = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.EN_ATTENTE
    )

    tickets_resolus = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.RESOLU
    )

    tickets_fermes = sum(
        1 for ticket in tickets
        if ticket.statut == StatutTicket.FERME
    )

    # =========================
    # STATISTIQUES PAR PRIORITÉ
    # =========================
    priorites = {
        "Faible": 0,
        "Moyenne": 0,
        "Haute": 0,
        "Critique": 0
    }

    for ticket in tickets:
        if ticket.priorite == PrioriteTicket.FAIBLE:
            priorites["Faible"] += 1

        elif ticket.priorite == PrioriteTicket.MOYENNE:
            priorites["Moyenne"] += 1

        elif ticket.priorite == PrioriteTicket.HAUTE:
            priorites["Haute"] += 1

        elif ticket.priorite == PrioriteTicket.CRITIQUE:
            priorites["Critique"] += 1

    # =========================
    # STATISTIQUES PAR CATÉGORIE
    # =========================
    categories = Categorie.query.order_by(
        Categorie.nom.asc()
    ).all()

    statistiques_categories = {}

    for categorie in categories:
        statistiques_categories[categorie.nom] = len(
            categorie.tickets
        )




    # =========================
    # STATISTIQUES PAR SERVICE
    # =========================
    statistiques_services = {}

    for ticket in tickets:

        if ticket.demandeur and ticket.demandeur.service:
            service = ticket.demandeur.service.strip()

            statistiques_services[service] = (
                statistiques_services.get(service, 0) + 1
            )
    # =========================
    # STATISTIQUES TECHNICIENS
    # =========================
    techniciens = Utilisateur.query.filter_by(
        role=RoleUtilisateur.TECHNICIEN
    ).order_by(Utilisateur.nom.asc()).all()

    statistiques_techniciens = []

    for technicien in techniciens:

        tickets_technicien = technicien.tickets_assignes

        total = len(tickets_technicien)

        en_cours = sum(
            1 for ticket in tickets_technicien
            if ticket.statut in [
                StatutTicket.ASSIGNE,
                StatutTicket.EN_COURS,
                StatutTicket.EN_ATTENTE
            ]
        )

        resolus = sum(
            1 for ticket in tickets_technicien
            if ticket.statut in [
                StatutTicket.RESOLU,
                StatutTicket.FERME
            ]
        )

        statistiques_techniciens.append({
            "nom": technicien.nom,
            "total": total,
            "en_cours": en_cours,
            "resolus": resolus
        })

    return render_template(
        "admin/statistiques.html",

        total_tickets=total_tickets,

        tickets_nouveaux=tickets_nouveaux,
        tickets_assignes=tickets_assignes,
        tickets_en_cours=tickets_en_cours,
        tickets_en_attente=tickets_en_attente,
        tickets_resolus=tickets_resolus,
        tickets_fermes=tickets_fermes,

        priorites=priorites,

        statistiques_categories=statistiques_categories,
        statistiques_services=statistiques_services,
        statistiques_techniciens=statistiques_techniciens
        
    )


@app.route("/admin/ticket/<int:ticket_id>/fermer", methods=["POST"])
@login_required
def fermer_ticket_admin(ticket_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.statut != StatutTicket.RESOLU:
        flash("Seuls les tickets résolus peuvent être fermés.")
        return redirect(url_for("admin_tickets"))

    ancien_statut = ticket.statut
    ticket.statut = StatutTicket.FERME

    historique = HistoriqueTicket(
        action=f"Résolution validée : {ancien_statut.value} → FERME",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

    notification_user = Notification(
        message=f"Votre ticket #{ticket.id} a été validé et fermé par l'administrateur.",
        utilisateur_id=ticket.demandeur_id,
        ticket_id=ticket.id
    )

    db.session.add(notification_user)

    if ticket.technicien_id:
        notification_technicien = Notification(
            message=f"La résolution du ticket #{ticket.id} a été validée par l'administrateur.",
            utilisateur_id=ticket.technicien_id,
            ticket_id=ticket.id
        )

        db.session.add(notification_technicien)

    db.session.commit()

    flash("Résolution validée et ticket fermé avec succès.")

    return redirect(url_for("admin_tickets"))


@app.route("/admin/ticket/<int:ticket_id>/valider-resolution", methods=["POST"])
@login_required
def valider_resolution_admin(ticket_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.statut != StatutTicket.RESOLU:
        flash("Ce ticket n'est pas en attente de validation.")
        return redirect(url_for("admin_tickets"))

    ticket.statut = StatutTicket.FERME

    historique = HistoriqueTicket(
        action="Résolution validée par l'administrateur : RESOLU → FERME",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

    notification_user = Notification(
        message=f"Votre ticket #{ticket.id} a été validé et fermé.",
        utilisateur_id=ticket.demandeur_id,
        ticket_id=ticket.id
    )
    db.session.add(notification_user)

    if ticket.technicien_id:
        notification_technicien = Notification(
            message=f"La résolution du ticket #{ticket.id} a été validée par l'administrateur.",
            utilisateur_id=ticket.technicien_id,
            ticket_id=ticket.id
        )
        db.session.add(notification_technicien)

    db.session.commit()

    flash("Résolution validée avec succès.")
    return redirect(url_for("admin_tickets"))

@app.route("/admin/ticket/<int:ticket_id>/refuser-resolution", methods=["POST"])
@login_required
def refuser_resolution_admin(ticket_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.statut != StatutTicket.RESOLU:
        flash("Ce ticket n'est pas en attente de validation.")
        return redirect(url_for("admin_tickets"))

    motif = request.form.get("motif_refus", "").strip()

    if not motif:
        flash("Veuillez indiquer le motif du refus.")
        return redirect(url_for("admin_tickets"))

    ticket.statut = StatutTicket.EN_COURS
    ticket.date_resolution = None

    historique = HistoriqueTicket(
        action=f"Résolution refusée par l'administrateur : {motif}",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

    if ticket.technicien_id:
        notification_technicien = Notification(
            message=f"Résolution refusée pour le ticket #{ticket.id}. Motif : {motif}",
            utilisateur_id=ticket.technicien_id,
            ticket_id=ticket.id
        )
        db.session.add(notification_technicien)

    db.session.commit()

    flash("Résolution refusée. Le ticket est retourné au technicien.")
    return redirect(url_for("admin_tickets"))

@app.route("/admin/historique")
@login_required
def admin_historique():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    historiques = (
        HistoriqueTicket.query
        .order_by(HistoriqueTicket.date_action.desc())
        .all()
    )

    return render_template(
        "admin/historique.html",
        historiques=historiques
    )



@app.route("/admin/notifications")
@login_required
def admin_notifications():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    notifications = (
        Notification.query
        .filter_by(utilisateur_id=current_user.id)
        .order_by(Notification.date_creation.desc())
        .all()
    )

    return render_template(
        "admin/notifications.html",
        notifications=notifications
    )


@app.route("/admin/notifications/<int:notification_id>/lire", methods=["POST"])
@login_required
def admin_lire_notification(notification_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    notification = Notification.query.get_or_404(notification_id)

    if notification.utilisateur_id != current_user.id:
        flash("Notification non autorisée.")
        return redirect(url_for("admin_notifications"))

    notification.lu = True
    db.session.commit()

    return redirect(url_for("admin_notifications"))


@app.route("/admin/utilisateurs")
@login_required
def admin_utilisateurs():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Texte saisi dans la barre de recherche
    recherche = request.args.get("q", "").strip()

    query = Utilisateur.query

    # Recherche par nom OU email
    if recherche:
        query = query.filter(
            db.or_(
                Utilisateur.nom.ilike(f"%{recherche}%"),
                Utilisateur.email.ilike(f"%{recherche}%")
            )
        )

    utilisateurs = (
        query
        .order_by(Utilisateur.date_creation.desc())
        .all()
    )

    return render_template(
        "admin/utilisateurs.html",
        utilisateurs=utilisateurs,
        recherche=recherche
    )

@app.route("/admin/techniciens")
@login_required
def admin_techniciens():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Récupérer la recherche
    recherche = request.args.get("q", "").strip()

    # Garder uniquement les techniciens
    query = Utilisateur.query.filter_by(
        role=RoleUtilisateur.TECHNICIEN
    )

    # Recherche par nom OU email
    if recherche:
        query = query.filter(
            db.or_(
                Utilisateur.nom.ilike(f"%{recherche}%"),
                Utilisateur.email.ilike(f"%{recherche}%")
            )
        )

    techniciens = (
        query
        .order_by(Utilisateur.nom.asc())
        .all()
    )

    return render_template(
        "admin/techniciens.html",
        techniciens=techniciens,
        StatutTicket=StatutTicket,
        recherche=recherche
    )






@app.route("/admin/categories")
@login_required
def admin_categories():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Récupérer la recherche
    recherche = request.args.get("q", "").strip()

    query = Categorie.query

    # Recherche par nom OU description
    if recherche:
        query = query.filter(
            db.or_(
                Categorie.nom.ilike(f"%{recherche}%"),
                Categorie.description.ilike(f"%{recherche}%")
            )
        )

    categories = (
        query
        .order_by(Categorie.nom.asc())
        .all()
    )

    return render_template(
        "admin/categories.html",
        categories=categories,
        recherche=recherche
    )


@app.route("/admin/categories/<int:categorie_id>/modifier", methods=["POST"])
@login_required
def modifier_categorie(categorie_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    categorie = Categorie.query.get_or_404(categorie_id)

    nom = request.form.get("nom", "").strip()
    description = request.form.get("description", "").strip()

    if not nom:
        flash("Le nom de la catégorie est obligatoire.")
        return redirect(url_for("admin_categories"))

    categorie.nom = nom
    categorie.description = description

    db.session.commit()

    flash("Catégorie modifiée avec succès.")

    return redirect(url_for("admin_categories"))


@app.route("/admin/categories/<int:categorie_id>/supprimer", methods=["POST"])
@login_required
def supprimer_categorie(categorie_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    categorie = Categorie.query.get_or_404(categorie_id)

    if categorie.tickets:
        flash("Impossible de supprimer une catégorie utilisée par des tickets.")
        return redirect(url_for("admin_categories"))

    db.session.delete(categorie)
    db.session.commit()

    flash("Catégorie supprimée avec succès.")

    return redirect(url_for("admin_categories"))

@app.route("/admin/categories/ajouter", methods=["POST"])
@login_required
def admin_ajouter_categorie():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    nom = request.form.get("nom", "").strip()
    description = request.form.get("description", "").strip()

    if not nom:
        flash("Le nom de la catégorie est obligatoire.")
        return redirect(url_for("admin_categories"))

    categorie_existante = Categorie.query.filter_by(nom=nom).first()

    if categorie_existante:
        flash("Cette catégorie existe déjà.")
        return redirect(url_for("admin_categories"))

    categorie = Categorie(
        nom=nom,
        description=description or None
    )

    db.session.add(categorie)
    db.session.commit()

    flash("Catégorie ajoutée avec succès.")

    return redirect(url_for("admin_categories"))


@app.route("/admin/utilisateurs/ajouter", methods=["POST"])
@login_required
def admin_ajouter_utilisateur():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Récupération des données du formulaire
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip().lower()
    mot_de_passe = request.form.get("mot_de_passe", "").strip()
    role = request.form.get("role", "").strip()
    service = request.form.get("service", "").strip()

    # Vérification des champs obligatoires
    if not nom or not email or not mot_de_passe or not role:
        flash("Veuillez remplir tous les champs.")
        return redirect(url_for("admin_utilisateurs"))

    # Vérification de l'unicité de l'adresse email
    if Utilisateur.query.filter_by(email=email).first():
        flash("Cette adresse email est déjà utilisée.")
        return redirect(url_for("admin_utilisateurs"))

    # Vérification du rôle
    try:
        role_enum = RoleUtilisateur[role]
    except KeyError:
        flash("Rôle invalide.")
        return redirect(url_for("admin_utilisateurs"))

    # Le service est obligatoire uniquement pour les utilisateurs
    if role_enum == RoleUtilisateur.USER and not service:
        flash("Le service est obligatoire pour un utilisateur.")
        return redirect(url_for("admin_utilisateurs"))

    # Création de l'utilisateur
    utilisateur = Utilisateur(
        nom=nom,
        email=email,
        role=role_enum,
        service=service if role_enum == RoleUtilisateur.USER else None
    )

    utilisateur.set_password(mot_de_passe)

    db.session.add(utilisateur)
    db.session.commit()

    # Email envoyé au nouvel utilisateur
    msg = Message(
        subject="Création de votre compte - Ticket Management",
        recipients=[utilisateur.email],
        body=f"""
Bonjour {utilisateur.nom},

Votre compte a été créé avec succès sur la plateforme Ticket Management.

Adresse email : {utilisateur.email}
Rôle : {utilisateur.role.value}
Service : {utilisateur.service if utilisateur.service else "Non applicable"}

Vous pouvez maintenant accéder à la plateforme avec votre compte.

Cordialement,
Ticket Management
"""
    )

    try:
        mail.send(msg)
    except Exception as e:
        app.logger.error(
            "Erreur lors de l'envoi de l'email à %s : %s",
            utilisateur.email,
            e
        )

    flash("Utilisateur ajouté avec succès.")
    return redirect(url_for("admin_utilisateurs"))


@app.route(
    "/admin/utilisateurs/<int:utilisateur_id>/supprimer",
    methods=["POST"]
)
@login_required
def supprimer_utilisateur(utilisateur_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    utilisateur = Utilisateur.query.get_or_404(utilisateur_id)

    if utilisateur.id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.")
        return redirect(url_for("admin_utilisateurs"))

    if (
        utilisateur.tickets_crees
        or utilisateur.tickets_assignes
        or utilisateur.commentaires
        or utilisateur.notifications
    ):
        flash(
            "Impossible de supprimer cet utilisateur car "
            "il possède des données associées."
        )
        return redirect(url_for("admin_utilisateurs"))

    db.session.delete(utilisateur)
    db.session.commit()

    flash("Utilisateur supprimé avec succès.")

    return redirect(url_for("admin_utilisateurs"))

@app.route(
    "/admin/utilisateurs/<int:utilisateur_id>/modifier",
    methods=["POST"]
)
@login_required
def modifier_utilisateur(utilisateur_id):

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    utilisateur = Utilisateur.query.get_or_404(utilisateur_id)

    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "").strip()
    nouveau_mot_de_passe = request.form.get(
        "mot_de_passe",
        ""
    ).strip()

    if not nom or not email or not role:
        flash("Nom, email et rôle sont obligatoires.")
        return redirect(url_for("admin_utilisateurs"))

    email_existant = Utilisateur.query.filter(
        Utilisateur.email == email,
        Utilisateur.id != utilisateur.id
    ).first()

    if email_existant:
        flash("Cette adresse email est déjà utilisée.")
        return redirect(url_for("admin_utilisateurs"))

    try:
        role_enum = RoleUtilisateur[role]
    except KeyError:
        flash("Rôle invalide.")
        return redirect(url_for("admin_utilisateurs"))

    utilisateur.nom = nom
    utilisateur.email = email
    utilisateur.role = role_enum

    if nouveau_mot_de_passe:
        utilisateur.set_password(nouveau_mot_de_passe)

    db.session.commit()

    flash("Utilisateur modifié avec succès.")

    return redirect(url_for("admin_utilisateurs"))

@app.route(
    "/admin/utilisateurs/<int:utilisateur_id>/modifier",
    methods=["POST"]
)



@app.route("/admin/profil", methods=["GET", "POST"])
@login_required
def admin_profil():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()

        ancien_mdp = request.form.get("ancien_mot_de_passe", "")
        nouveau_mdp = request.form.get("nouveau_mot_de_passe", "")
        confirmation = request.form.get("confirmation_mot_de_passe", "")

        if not nom or not email:
            flash("Le nom et l'email sont obligatoires.")
            return redirect(url_for("admin_profil"))

        email_existant = (
            Utilisateur.query
            .filter(
                Utilisateur.email == email,
                Utilisateur.id != current_user.id
            )
            .first()
        )

        if email_existant:
            flash("Cet email est déjà utilisé.")
            return redirect(url_for("admin_profil"))

        # Modification du mot de passe uniquement si un nouveau est saisi
        if nouveau_mdp:

            if not ancien_mdp:
                flash("Saisissez votre mot de passe actuel.")
                return redirect(url_for("admin_profil"))

            if not current_user.check_password(ancien_mdp):
                flash("Le mot de passe actuel est incorrect.")
                return redirect(url_for("admin_profil"))

            if len(nouveau_mdp) < 6:
                flash("Le nouveau mot de passe doit contenir au moins 6 caractères.")
                return redirect(url_for("admin_profil"))

            if nouveau_mdp != confirmation:
                flash("La confirmation du mot de passe est incorrecte.")
                return redirect(url_for("admin_profil"))

            current_user.set_password(nouveau_mdp)

        current_user.nom = nom
        current_user.email = email

        db.session.commit()

        flash("Profil mis à jour avec succès.")
        return redirect(url_for("admin_profil"))

    return render_template("admin/profil.html")

@app.route("/technicien/ticket/<int:ticket_id>/statut", methods=["POST"])
@login_required
def modifier_statut_ticket(ticket_id):

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.filter_by(
        id=ticket_id,
        technicien_id=current_user.id
    ).first_or_404()

    nouveau_statut = request.form.get("statut", "").strip()
    solution = request.form.get("solution_resolution", "").strip()

    statuts_autorises = {
        "EN_COURS": StatutTicket.EN_COURS,
        "EN_ATTENTE": StatutTicket.EN_ATTENTE,
        "RESOLU": StatutTicket.RESOLU
    }

    if nouveau_statut not in statuts_autorises:
        flash("Statut invalide.")
        return redirect(
            url_for(
                "dashboard_technicien",
                ticket=ticket.id
            )
        )

    # Une solution est obligatoire pour résoudre un ticket
    if nouveau_statut == "RESOLU" and not solution:
        flash(
            "Veuillez indiquer la solution appliquée avant de résoudre le ticket."
        )
        return redirect(
            url_for(
                "dashboard_technicien",
                ticket=ticket.id
            )
        )

    ancien_statut = ticket.statut
    ticket.statut = statuts_autorises[nouveau_statut]

    if ticket.statut == StatutTicket.RESOLU:
        ticket.date_resolution = datetime.utcnow()
        ticket.solution_resolution = solution

    else:
        ticket.date_resolution = None

    # Historique
    historique = HistoriqueTicket(
        action=(
            f"Statut modifié : "
            f"{ancien_statut.value} → {ticket.statut.value}"
        ),
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

    # Notification utilisateur
    notification = Notification(
        message=(
            f"Le statut de votre ticket #{ticket.id} "
            f"est maintenant : {ticket.statut.value}."
        ),
        utilisateur_id=ticket.demandeur_id,
        ticket_id=ticket.id
    )

    db.session.add(notification)

    db.session.commit()

    flash("Statut du ticket mis à jour avec succès.")

    if nouveau_statut == "EN_COURS":
    

     return redirect(
        url_for(
        "dashboard_technicien",
        ticket=ticket.id
        )
    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return "Application de gestion des tickets"
@app.route("/user/tickets/new", methods=["GET", "POST"])
@login_required
def creer_ticket():

    # Vérifier que l'utilisateur connecté est bien un USER
    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Charger les catégories
    categories = (
        Categorie.query
        .order_by(Categorie.nom.asc())
        .all()
    )

    if request.method == "POST":

        # Récupérer les données du formulaire
        titre = request.form.get("titre", "").strip()
        description = request.form.get("description", "").strip()
        priorite = request.form.get("priorite", "").strip()
        categorie_id = request.form.get("categorie_id", "").strip()
        autre_categorie = request.form.get("autre_categorie", "").strip()
        localisation = request.form.get("localisation", "").strip()
        equipement = request.form.get("equipement", "").strip()

        # Vérification des champs obligatoires
        if (
            not titre
            or not description
            or not priorite
            or not categorie_id
            or not localisation
        ):
            flash("Veuillez remplir tous les champs obligatoires.")

            return render_template(
                "user/create_ticket.html",
                categories=categories
            )

        # Vérifier que la catégorie existe
        try:
            categorie_id_int = int(categorie_id)

        except ValueError:
            flash("Catégorie invalide.")

            return render_template(
                "user/create_ticket.html",
                categories=categories
            )

        categorie = db.session.get(
            Categorie,
            categorie_id_int
        )

        if not categorie:
            flash("Catégorie invalide.")

            return render_template(
                "user/create_ticket.html",
                categories=categories
            )

# Gestion de la catégorie "Autre"
        if categorie.nom.strip().lower() == "autre":

            if not autre_categorie:
                flash("Veuillez préciser la catégorie.")

                return render_template(
            "user/create_ticket.html",
            categories=categories
        )

        else:
              autre_categorie = None

        # Vérifier que la priorité est valide
        try:
            priorite_ticket = PrioriteTicket[priorite]

        except KeyError:
            flash("Priorité invalide.")

            return render_template(
                "user/create_ticket.html",
                categories=categories
            )

        # Création du ticket
        ticket = Ticket(
            titre=titre,
            description=description,
            localisation=localisation,
            equipement=equipement or None,
            priorite=priorite_ticket,
            statut=StatutTicket.NOUVEAU,
            demandeur_id=current_user.id,
            categorie_id=categorie.id,
            autre_categorie=autre_categorie
        )

        db.session.add(ticket)

        # Récupérer ticket.id avant le commit
        db.session.flush()

        # Historique
        historique = HistoriqueTicket(
            action="Ticket créé",
            ticket_id=ticket.id,
            utilisateur_id=current_user.id
        )

        db.session.add(historique)

        # Récupérer les administrateurs
        admins = Utilisateur.query.filter_by(
            role=RoleUtilisateur.ADMIN
        ).all()

        # Notifications internes aux administrateurs
        for admin in admins:

            notification = Notification(
                message=(
                    f"Nouveau ticket #{ticket.id} créé par "
                    f"{current_user.nom} : {ticket.titre}"
                ),
                utilisateur_id=admin.id,
                ticket_id=ticket.id
            )

            db.session.add(notification)

        # Sauvegarder dans la base de données
        db.session.commit()

        # ==========================================
        # EMAIL SI LE TICKET EST CRITIQUE
        # ==========================================

        if ticket.priorite == PrioriteTicket.CRITIQUE:

            for admin in admins:

                if admin.email:

                    msg = Message(
                        subject=f"URGENT - Ticket critique #{ticket.id}",
                        recipients=[admin.email],
                        body=f"""
Bonjour {admin.nom},

Un nouveau ticket CRITIQUE vient d'être créé.

Ticket : #{ticket.id}
Titre : {ticket.titre}
Demandeur : {current_user.nom}
Catégorie : {categorie.nom}
Localisation : {ticket.localisation}
Équipement : {ticket.equipement or "Non renseigné"}

Description :
{ticket.description}

Veuillez consulter la plateforme Ticket Management.

Cordialement,
Ticket Management
"""
                    )

                    try:
                        mail.send(msg)

                    except Exception as e:
                        app.logger.error(
                            "Erreur lors de l'envoi de l'email critique #%s : %s",
                            ticket.id,
                            e
                        )

      


    # Confirmation affichée uniquement dans le dashboard
        flash(
    "Votre ticket a été créé avec succès.",
    "ticket_created"
)

        return redirect(
           url_for(
             "dashboard_user",
              ticket=ticket.id
    )
)

    # GET : afficher le formulaire
    return render_template(
        "user/create_ticket.html",
        categories=categories
    )
@app.route("/user/ticket/<int:ticket_id>/commentaire", methods=["POST"])
@login_required
def ajouter_commentaire(ticket_id):

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    ticket = Ticket.query.filter_by(
        id=ticket_id,
        demandeur_id=current_user.id
    ).first_or_404()

    contenu = request.form.get("contenu", "").strip()

    if not contenu:
        flash("Le commentaire ne peut pas être vide.")
        return redirect(
            url_for(
                "dashboard_user",
                ticket=ticket.id
            )
        )

    commentaire = Commentaire(
        contenu=contenu,
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(commentaire)

    historique = HistoriqueTicket(
        action="Commentaire ajouté",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)
    db.session.commit()

    flash("Commentaire ajouté avec succès.")

    return redirect(
        url_for(
            "dashboard_user",
            ticket=ticket.id
        )
    )


@app.route("/user/historique")
@login_required
def historique_user():

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    historiques = (
        HistoriqueTicket.query
        .join(Ticket)
        .filter(Ticket.demandeur_id == current_user.id)
        .order_by(HistoriqueTicket.date_action.desc())
        .all()
    )

    return render_template(
        "user/historique.html",
        historiques=historiques
    )


@app.route("/user/notifications")
@login_required
def notifications_user():

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    notifications = (
        Notification.query
        .filter_by(utilisateur_id=current_user.id)
        .order_by(Notification.date_creation.desc())
        .all()
    )

    return render_template(
        "user/notifications.html",
        notifications=notifications
    )



@app.route("/user/profil", methods=["GET", "POST"])
@login_required
def profil_user():

    if current_user.role != RoleUtilisateur.USER:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        nouveau_mot_de_passe = request.form.get(
            "nouveau_mot_de_passe", ""
        ).strip()

        if not nom or not email:
            flash("Le nom et l'email sont obligatoires.")
            return redirect(url_for("profil_user"))

        # Vérifier que l'email n'est pas utilisé par un autre compte
        utilisateur_existant = (
            Utilisateur.query
            .filter(
                Utilisateur.email == email,
                Utilisateur.id != current_user.id
            )
            .first()
        )

        if utilisateur_existant:
            flash("Cette adresse email est déjà utilisée.")
            return redirect(url_for("profil_user"))

        current_user.nom = nom
        current_user.email = email

        # Modifier le mot de passe seulement si un nouveau est saisi
        if nouveau_mot_de_passe:
            current_user.set_password(nouveau_mot_de_passe)

        db.session.commit()

        flash("Profil mis à jour avec succès.")

        return redirect(url_for("profil_user"))

    return render_template(
        "user/profil.html"
    )













@app.route("/test-email")
def test_email():
    msg = Message(
        subject="Test vers une autre adresse",
        recipients=["basmaelkasimi5@gmail.com"],
        body="Test Flask-Mail vers une adresse différente."
    )

    mail.send(msg)

    return "Email envoyé"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
