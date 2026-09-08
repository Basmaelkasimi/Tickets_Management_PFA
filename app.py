from flask import Flask

from flask_login import LoginManager
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime

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


app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tickets.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret-key"

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
        tickets_attente=tickets_attente,
        tickets_resolus=tickets_resolus,
        selected_ticket=selected_ticket
    )


@app.route("/technicien/dashboard")
@login_required
def dashboard_technicien():

    if current_user.role != RoleUtilisateur.TECHNICIEN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    # Tous les tickets assignés au technicien
    all_tickets = (
        Ticket.query
        .filter_by(technicien_id=current_user.id)
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    # Statistiques
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

    # Recherche
    recherche = request.args.get("q", "").strip()

    # Filtre statut
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

    # Filtre par statut
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

    # Ticket sélectionné
    ticket_id = request.args.get("ticket", type=int)

    selected_ticket = None

    if ticket_id:
        selected_ticket = Ticket.query.filter_by(
            id=ticket_id,
            technicien_id=current_user.id
        ).first()

    # Premier ticket par défaut
    if selected_ticket is None and tickets:
        selected_ticket = tickets[0]

    return render_template(
        "technicien/dashboard.html",
        tickets=tickets,
        total_tickets=total_tickets,
        tickets_en_cours=tickets_en_cours,
        tickets_attente=tickets_attente,
        tickets_resolus=tickets_resolus,
        selected_ticket=selected_ticket
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

    # Notification technicien
    notification = Notification(
        message=f"Le ticket #{ticket.id} vous a été assigné.",
        utilisateur_id=technicien.id,
        ticket_id=ticket.id
    )

    db.session.add(notification)

    db.session.commit()

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

    tickets = (
        Ticket.query
        .order_by(Ticket.date_creation.desc())
        .all()
    )

    techniciens = (
        Utilisateur.query
        .filter_by(role=RoleUtilisateur.TECHNICIEN)
        .order_by(Utilisateur.nom)
        .all()
    )

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

    recherche = request.args.get("q", "").strip()
    statut = request.args.get("statut", "").strip()

    query = Ticket.query

    # Recherche par titre
    if recherche:
        query = query.filter(
            Ticket.titre.ilike(f"%{recherche}%")
        )

    # Filtre par statut
    if statut:
        try:
            query = query.filter(
                Ticket.statut == StatutTicket(statut)
            )
        except ValueError:
            pass

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

    return render_template(
        "admin/tickets.html",
        tickets=tickets,
        techniciens=techniciens,
        recherche=recherche,
        statut_selectionne=statut,
        statuts=StatutTicket
    )

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

    utilisateurs = (
        Utilisateur.query
        .order_by(Utilisateur.date_creation.desc())
        .all()
    )

    return render_template(
        "admin/utilisateurs.html",
        utilisateurs=utilisateurs
    )



@app.route("/admin/techniciens")
@login_required
def admin_techniciens():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    techniciens = (
        Utilisateur.query
        .filter_by(role=RoleUtilisateur.TECHNICIEN)
        .order_by(Utilisateur.nom.asc())
        .all()
    )

    return render_template(
        "admin/techniciens.html",
        techniciens=techniciens,
        StatutTicket=StatutTicket
    )



@app.route("/admin/categories")
@login_required
def admin_categories():

    if current_user.role != RoleUtilisateur.ADMIN:
        flash("Accès non autorisé.")
        return redirect(url_for("login"))

    categories = (
        Categorie.query
        .order_by(Categorie.nom.asc())
        .all()
    )

    return render_template(
        "admin/categories.html",
        categories=categories
    )

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

    ancien_statut = ticket.statut
    ticket.statut = statuts_autorises[nouveau_statut]

    if ticket.statut == StatutTicket.RESOLU:
        ticket.date_resolution = datetime.utcnow()
    else:
        ticket.date_resolution = None

    historique = HistoriqueTicket(
        action=f"Statut modifié : {ancien_statut.value} → {ticket.statut.value}",
        ticket_id=ticket.id,
        utilisateur_id=current_user.id
    )

    db.session.add(historique)

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

    flash("Statut du ticket mis à jour.")

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
    categories = Categorie.query.order_by(Categorie.nom).all()

    if request.method == "POST":

        titre = request.form.get("titre", "").strip()
        description = request.form.get("description", "").strip()
        priorite = request.form.get("priorite")
        categorie_id = request.form.get("categorie_id")

        # Vérification des champs
        if not titre or not description or not priorite or not categorie_id:

            flash("Veuillez remplir tous les champs obligatoires.")

            return render_template(
                "user/create_ticket.html",
                categories=categories
            )

        # Vérifier que la catégorie existe
        categorie = db.session.get(
            Categorie,
            int(categorie_id)
        )

        if not categorie:

            flash("Catégorie invalide.")

            return render_template(
                "user/create_ticket.html",
                categories=categories
            )

        # Création du ticket
        ticket = Ticket(
            titre=titre,
            description=description,
            priorite=PrioriteTicket[priorite],
            statut=StatutTicket.NOUVEAU,
            demandeur_id=current_user.id,
            categorie_id=categorie.id
        )

        db.session.add(ticket)

        # Permet de récupérer ticket.id avant le commit
        db.session.flush()

        # -------------------------------
        # HISTORIQUE
        # -------------------------------

        historique = HistoriqueTicket(
            action="Ticket créé",
            ticket_id=ticket.id,
            utilisateur_id=current_user.id
        )

        db.session.add(historique)

        # -------------------------------
        # NOTIFICATION ADMIN
        # -------------------------------

        admins = Utilisateur.query.filter_by(
            role=RoleUtilisateur.ADMIN
        ).all()

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

        # Sauvegarder ticket + historique + notifications
        db.session.commit()

        flash("Votre ticket a été créé avec succès.")

        return redirect(url_for("dashboard_user"))

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

if __name__ == "__main__":
    app.run(debug=True)