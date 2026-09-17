from flask import Blueprint, jsonify, request

from app.models import Program, ProgramOption, StudyYear, ClassGroup, Center

academic_bp = Blueprint("academic", __name__, url_prefix="/api/academic")


@academic_bp.get("/centers")
def list_centers():
    centers = Center.query.filter_by(actif=True).order_by(Center.nom).all()
    return jsonify({"items": [c.to_dict() for c in centers]})


@academic_bp.get("/programs")
def list_programs():
    programs = Program.query.filter_by(actif=True).order_by(Program.nom).all()
    return jsonify({"items": [p.to_dict() for p in programs]})


@academic_bp.get("/options")
def list_options():
    program_id = request.args.get("program_id")
    if not program_id:
        return jsonify({"message": "program_id est requis."}), 400

    options = (
        ProgramOption.query.filter_by(program_id=program_id, actif=True)
        .order_by(ProgramOption.nom)
        .all()
    )
    return jsonify({"items": [o.to_dict() for o in options]})


@academic_bp.get("/study-years")
def list_study_years():
    years = StudyYear.query.order_by(StudyYear.niveau).all()
    return jsonify({"items": [y.to_dict() for y in years]})


@academic_bp.get("/classes")
def list_classes():
    option_id = request.args.get("option_id")
    study_year_id = request.args.get("study_year_id")
    centre_id = request.args.get("centre_id")
    if not option_id or not study_year_id or not centre_id:
        return jsonify({"message": "centre_id, option_id et study_year_id sont requis."}), 400

    classes = ClassGroup.query.filter_by(
        centre_id=centre_id, option_id=option_id, study_year_id=study_year_id, actif=True
    ).all()
    return jsonify({"items": [c.to_dict() for c in classes]})