from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Program, StudyYear, TeachingUnit, Subject
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------- Unités d'Enseignement (UE) ----------

@admin_bp.get("/teaching-units")
@role_required("admin")
def list_teaching_units():
    program_id = request.args.get("program_id")
    study_year_id = request.args.get("study_year_id")

    query = TeachingUnit.query
    if program_id:
        query = query.filter_by(program_id=program_id)
    if study_year_id:
        query = query.filter_by(study_year_id=study_year_id)

    items = query.order_by(TeachingUnit.nom).all()
    return jsonify({"items": [u.to_dict() for u in items]})


@admin_bp.post("/teaching-units")
@role_required("admin")
def create_teaching_unit():
    data = request.get_json(silent=True) or {}
    required = ["nom", "program_id", "study_year_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if not Program.query.get(data["program_id"]):
        return jsonify({"message": "Filière introuvable."}), 404
    if not StudyYear.query.get(data["study_year_id"]):
        return jsonify({"message": "Année d'étude introuvable."}), 404

    existing = TeachingUnit.query.filter_by(
        program_id=data["program_id"],
        study_year_id=data["study_year_id"],
        nom=data["nom"],
    ).first()
    if existing:
        return jsonify({"message": "Cette UE existe déjà pour cette filière/année."}), 409

    ue = TeachingUnit(
        nom=data["nom"],
        code=data.get("code"),
        program_id=data["program_id"],
        study_year_id=data["study_year_id"],
    )
    db.session.add(ue)
    db.session.commit()

    return jsonify(ue.to_dict()), 201


@admin_bp.patch("/teaching-units/<ue_id>")
@role_required("admin")
def update_teaching_unit(ue_id):
    ue = TeachingUnit.query.get(ue_id)
    if not ue:
        return jsonify({"message": "UE introuvable."}), 404

    data = request.get_json(silent=True) or {}
    for field in ("nom", "code", "actif"):
        if field in data:
            setattr(ue, field, data[field])

    db.session.commit()
    return jsonify(ue.to_dict())


@admin_bp.delete("/teaching-units/<ue_id>")
@role_required("admin")
def delete_teaching_unit(ue_id):
    ue = TeachingUnit.query.get(ue_id)
    if not ue:
        return jsonify({"message": "UE introuvable."}), 404

    db.session.delete(ue)
    db.session.commit()
    return jsonify({"message": "UE supprimée."})


# ---------- Matières ----------

@admin_bp.get("/subjects")
@role_required("admin")
def list_subjects():
    ue_id = request.args.get("ue_id")
    query = Subject.query
    if ue_id:
        query = query.filter_by(ue_id=ue_id)

    items = query.order_by(Subject.nom).all()
    return jsonify({"items": [s.to_dict() for s in items]})


@admin_bp.post("/subjects")
@role_required("admin")
def create_subject():
    data = request.get_json(silent=True) or {}
    required = ["nom", "ue_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    ue = TeachingUnit.query.get(data["ue_id"])
    if not ue:
        return jsonify({"message": "UE introuvable."}), 404

    subject = Subject(nom=data["nom"], ue_id=ue.id)
    db.session.add(subject)
    db.session.commit()

    return jsonify(subject.to_dict()), 201


@admin_bp.patch("/subjects/<subject_id>")
@role_required("admin")
def update_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"message": "Matière introuvable."}), 404

    data = request.get_json(silent=True) or {}
    if "nom" in data:
        subject.nom = data["nom"]
    if "ue_id" in data:
        if not TeachingUnit.query.get(data["ue_id"]):
            return jsonify({"message": "UE introuvable."}), 404
        subject.ue_id = data["ue_id"]

    db.session.commit()
    return jsonify(subject.to_dict())


@admin_bp.delete("/subjects/<subject_id>")
@role_required("admin")
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({"message": "Matière introuvable."}), 404

    db.session.delete(subject)
    db.session.commit()
    return jsonify({"message": "Matière supprimée."})