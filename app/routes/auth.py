import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    User,
    RoleEnum,
    AccountStatusEnum,
    Student,
    Teacher,
    VerificationDocument,
    ClassGroup,
    Program,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    mot_de_passe = data.get("mot_de_passe") or ""

    if not email or not mot_de_passe:
        return jsonify({"message": "E-mail et mot de passe requis."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(mot_de_passe):
        return jsonify({"message": "E-mail ou mot de passe incorrect."}), 401

    if user.statut != AccountStatusEnum.VALIDE:
        return (
            jsonify(
                {
                    "message": "Compte non actif.",
                    "statut": user.statut.value,
                }
            ),
            403,
        )

    access_token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role.value, "statut": user.statut.value},
    )

    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200


@auth_bp.post("/register/student")
def register_student():
    """
    Inscription étudiant (multipart/form-data) :
      nom_complet, email, telephone, mot_de_passe, confirmation_mot_de_passe,
      classe_id, annee_inscription, justificatif (fichier)
    """
    form = request.form
    required_fields = [
        "nom_complet",
        "email",
        "mot_de_passe",
        "confirmation_mot_de_passe",
        "classe_id",
        "annee_inscription",
    ]
    missing = [f for f in required_fields if not form.get(f)]
    if missing:
        return (
            jsonify({"message": f"Champs manquants : {', '.join(missing)}"}),
            400,
        )

    if form["mot_de_passe"] != form["confirmation_mot_de_passe"]:
        return jsonify({"message": "Les mots de passe ne correspondent pas."}), 400

    email = form["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Cet e-mail est déjà utilisé."}), 409

    classe = ClassGroup.query.get(form["classe_id"])
    if not classe:
        return jsonify({"message": "Classe introuvable."}), 404

    justificatif = request.files.get("justificatif")
    if not justificatif or justificatif.filename == "":
        return jsonify({"message": "Le justificatif d'inscription est obligatoire."}), 400
    if not _allowed_file(
        justificatif.filename, current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"]
    ):
        return jsonify({"message": "Format de justificatif non autorisé."}), 400

    user = User(
        nom_complet=form["nom_complet"],
        email=email,
        telephone=form.get("telephone"),
        role=RoleEnum.ETUDIANT,
        statut=AccountStatusEnum.EN_ATTENTE,
    )
    user.set_password(form["mot_de_passe"])
    db.session.add(user)
    db.session.flush()  # pour obtenir user.id avant le commit

    student = Student(
        user_id=user.id,
        annee_inscription=form["annee_inscription"],
        classe_id=classe.id,
    )
    db.session.add(student)

    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "justificatifs")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"{user.id}_{justificatif.filename}")
    justificatif.save(os.path.join(upload_dir, filename))

    verification_doc = VerificationDocument(
        user_id=user.id,
        type="justificatif_inscription",
        fichier=filename,
        statut="en_attente",
        date_upload=datetime.utcnow(),
    )
    db.session.add(verification_doc)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Inscription reçue. Votre compte est en attente de validation.",
                "user": user.to_dict(),
            }
        ),
        201,
    )


@auth_bp.post("/register/teacher")
def register_teacher():
    """
    Inscription enseignant (multipart/form-data) :
      nom_complet, email, telephone, mot_de_passe, confirmation_mot_de_passe,
      departement_id (filière), fonction, matieres_declarees, justificatif (fichier)
    """
    form = request.form
    required_fields = [
        "nom_complet",
        "email",
        "mot_de_passe",
        "confirmation_mot_de_passe",
        "departement_id",
        "matieres_declarees",
    ]
    missing = [f for f in required_fields if not form.get(f)]
    if missing:
        return (
            jsonify({"message": f"Champs manquants : {', '.join(missing)}"}),
            400,
        )

    if form["mot_de_passe"] != form["confirmation_mot_de_passe"]:
        return jsonify({"message": "Les mots de passe ne correspondent pas."}), 400

    email = form["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Cet e-mail est déjà utilisé."}), 409

    departement = Program.query.get(form["departement_id"])
    if not departement:
        return jsonify({"message": "Filière/département introuvable."}), 404

    justificatif = request.files.get("justificatif")
    if not justificatif or justificatif.filename == "":
        return (
            jsonify(
                {
                    "message": "Le justificatif prouvant votre statut d'enseignant est obligatoire."
                }
            ),
            400,
        )
    if not _allowed_file(
        justificatif.filename, current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"]
    ):
        return jsonify({"message": "Format de justificatif non autorisé."}), 400

    user = User(
        nom_complet=form["nom_complet"],
        email=email,
        telephone=form.get("telephone"),
        role=RoleEnum.ENSEIGNANT,
        statut=AccountStatusEnum.EN_ATTENTE,
    )
    user.set_password(form["mot_de_passe"])
    db.session.add(user)
    db.session.flush()

    teacher = Teacher(
        user_id=user.id,
        departement=departement.nom,
        fonction=form.get("fonction"),
        matieres_declarees=form["matieres_declarees"],
    )
    db.session.add(teacher)

    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "justificatifs")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"{user.id}_{justificatif.filename}")
    justificatif.save(os.path.join(upload_dir, filename))

    verification_doc = VerificationDocument(
        user_id=user.id,
        type="justificatif_enseignant",
        fichier=filename,
        statut="en_attente",
        date_upload=datetime.utcnow(),
    )
    db.session.add(verification_doc)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Inscription reçue. Votre compte est en attente de validation.",
                "user": user.to_dict(),
            }
        ),
        201,
    )