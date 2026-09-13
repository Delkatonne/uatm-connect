from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Document, Exam, Notification, Student, User, AcademicProgram, Grade
from app.utils.decorators import account_must_be_valide, role_required

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


def _current_student():
    user_id = get_jwt_identity()
    return Student.query.filter_by(user_id=user_id).first()


@student_bp.get("/me")
@role_required("etudiant")
@account_must_be_valide
def me():
    student = _current_student()
    if not student or not student.classe:
        return jsonify({"message": "Profil étudiant incomplet."}), 404

    return jsonify(
        {
            "nom_complet": student.user.nom_complet,
            "email": student.user.email,
            "telephone": student.user.telephone,
            "photo_profil": student.user.photo_profil,
            "annee_inscription": student.annee_inscription,
            "filiere": student.classe.option.program.nom,
            "option": student.classe.option.nom,
            "annee_etude": student.classe.study_year.nom,
            "classe": student.classe.nom,
        }
    )


@student_bp.patch("/me")
@role_required("etudiant")
@account_must_be_valide
def update_me():
    """Mise à jour des champs modifiables du profil (téléphone, photo)."""
    student = _current_student()
    if not student:
        return jsonify({"message": "Profil étudiant introuvable."}), 404

    if request.content_type and "multipart/form-data" in request.content_type:
        telephone = request.form.get("telephone")
        photo = request.files.get("photo")
        if telephone:
            student.user.telephone = telephone
        if photo and photo.filename:
            from werkzeug.utils import secure_filename
            import os as _os
            from flask import current_app as _app

            if not _allowed_photo(photo.filename):
                return jsonify({"message": "Format de photo non autorisé."}), 400
            upload_dir = _app.config["UPLOAD_FOLDER"] + "/photos"
            _os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"{student.user.id}_{photo.filename}")
            photo.save(_os.path.join(upload_dir, filename))
            student.user.photo_profil = filename
    else:
        data = request.get_json(silent=True) or {}
        if "telephone" in data:
            student.user.telephone = data["telephone"]

    db.session.commit()
    return jsonify({"message": "Profil mis à jour."})


def _allowed_photo(filename):
    from flask import current_app as _app

    allowed = _app.config["ALLOWED_IMAGE_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@student_bp.get("/documents")
@role_required("etudiant")
@account_must_be_valide
def documents():
    student = _current_student()
    if not student or not student.classe_id:
        return jsonify({"items": []})

    doc_type = request.args.get("type")
    query = Document.query.filter_by(class_id=student.classe_id)
    if doc_type:
        query = query.filter_by(type=doc_type)

    items = query.order_by(Document.date_publication.desc()).all()
    return jsonify({"items": [d.to_dict() for d in items]})


@student_bp.get("/exams")
@role_required("etudiant")
@account_must_be_valide
def exams():
    student = _current_student()
    if not student or not student.classe_id:
        return jsonify({"items": []})

    items = (
        Exam.query.filter_by(classe_id=student.classe_id)
        .order_by(Exam.date.asc())
        .all()
    )
    return jsonify({"items": [e.to_dict() for e in items]})


@student_bp.get("/programme")
@role_required("etudiant")
@account_must_be_valide
def programme():
    """Programme d'étude : matières regroupées par UE pour la filière/année de l'étudiant."""
    student = _current_student()
    if not student or not student.classe:
        return jsonify({"items": []})

    subjects = student.classe.matieres()
    grouped = {}
    for s in subjects:
        ue = s.teaching_unit
        if not ue:
            continue
        grouped.setdefault(ue.id, {"ue": ue.nom, "code": ue.code, "matieres": []})
        grouped[ue.id]["matieres"].append(s.nom)

    return jsonify({"items": list(grouped.values())})


@student_bp.patch("/notifications/<notif_id>/read")
@role_required("etudiant")
@account_must_be_valide
def mark_notification_read(notif_id):
    user_id = get_jwt_identity()
    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if not notif:
        return jsonify({"message": "Notification introuvable."}), 404

    notif.lu = True
    db.session.commit()
    return jsonify(notif.to_dict())
    user_id = get_jwt_identity()
    items = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.date.desc())
        .limit(30)
        .all()
    )
    return jsonify({"items": [n.to_dict() for n in items]})


@student_bp.get("/academic-programs")
@role_required("etudiant")
@account_must_be_valide
def academic_programs():
    """Programmes annuels, calendriers, notes de service reçus de l'administration."""
    student = _current_student()
    if not student:
        return jsonify({"items": []})

    items = AcademicProgram.query.filter(
        db.or_(
            db.and_(
                AcademicProgram.destinataire_type == "classe",
                AcademicProgram.destinataire_id == student.classe_id,
            ),
            AcademicProgram.destinataire_type == "role_etudiant",
            AcademicProgram.destinataire_type == "tous",
            db.and_(
                AcademicProgram.destinataire_type == "utilisateur",
                AcademicProgram.destinataire_id == get_jwt_identity(),
            ),
        )
    ).order_by(AcademicProgram.date_publication.desc()).all()

    return jsonify({"items": [a.to_dict() for a in items]})


@student_bp.get("/grades")
@role_required("etudiant")
@account_must_be_valide
def grades():
    """Mes notes : interrogations, sessions, sessions de rattrapage."""
    student = _current_student()
    if not student:
        return jsonify({"items": []})

    items = Grade.query.filter_by(student_id=student.id).all()
    return jsonify({"items": [g.to_dict() for g in items]})