from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models import Document, Exam, Notification, Student, User
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
            "filiere": student.classe.option.program.nom,
            "option": student.classe.option.nom,
            "annee_etude": student.classe.study_year.nom,
            "classe": student.classe.nom,
        }
    )


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


@student_bp.get("/notifications")
@role_required("etudiant")
@account_must_be_valide
def notifications():
    user_id = get_jwt_identity()
    items = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.date.desc())
        .limit(30)
        .all()
    )
    return jsonify({"items": [n.to_dict() for n in items]})
