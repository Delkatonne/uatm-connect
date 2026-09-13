import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    User,
    RoleEnum,
    AccountStatusEnum,
    Program,
    ProgramOption,
    StudyYear,
    TeachingUnit,
    Subject,
    Semester,
    Student,
    Teacher,
    ClassGroup,
    TeacherAssignment,
    ScheduleSlot,
    Notification,
    VerificationDocument,
    AcademicProgram,
    Exam,
    Grade,
)
from app.models.schedule import JOURS_SEMAINE
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------- Tableau de bord ----------

@admin_bp.get("/stats")
@role_required("admin")
def stats():
    return jsonify(
        {
            "etudiants": Student.query.count(),
            "enseignants": Teacher.query.count(),
            "comptes_en_attente": User.query.filter_by(
                statut=AccountStatusEnum.EN_ATTENTE
            ).count(),
            "comptes_valides": User.query.filter_by(
                statut=AccountStatusEnum.VALIDE
            ).count(),
            "comptes_refuses": User.query.filter_by(
                statut=AccountStatusEnum.REFUSE
            ).count(),
            "filieres": Program.query.count(),
            "options": ProgramOption.query.count(),
            "classes": ClassGroup.query.count(),
            "matieres": Subject.query.count(),
        }
    )


# ---------- Validation des comptes ----------

@admin_bp.get("/accounts")
@role_required("admin")
def list_accounts():
    statut = request.args.get("statut")  # en_attente_de_validation, valide, refuse, piece_a_fournir
    role = request.args.get("role")  # etudiant, enseignant

    query = User.query.filter(User.role != RoleEnum.ADMIN)
    if statut:
        query = query.filter_by(statut=AccountStatusEnum(statut))
    if role:
        query = query.filter_by(role=RoleEnum(role))

    users = query.order_by(User.date_creation.desc()).all()

    items = []
    for user in users:
        data = user.to_dict()
        docs = VerificationDocument.query.filter_by(user_id=user.id).all()
        data["justificatifs"] = [d.to_dict() for d in docs]
        if user.role == RoleEnum.ETUDIANT and user.student_profile:
            data["details"] = user.student_profile.to_dict()
        elif user.role == RoleEnum.ENSEIGNANT and user.teacher_profile:
            data["details"] = user.teacher_profile.to_dict()
        items.append(data)

    return jsonify({"items": items})


@admin_bp.get("/documents/<filename>")
@role_required("admin")
def download_justificatif(filename):
    upload_dir = current_app.config["UPLOAD_FOLDER"] + "/justificatifs"
    return send_from_directory(upload_dir, filename)


@admin_bp.post("/accounts/<user_id>/validate")
@role_required("admin")
def validate_account(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Compte introuvable."}), 404

    user.statut = AccountStatusEnum.VALIDE
    user.date_validation = datetime.utcnow()

    db.session.add(
        Notification(
            user_id=user.id,
            titre="Compte validé",
            message="Votre compte a été validé. Vous pouvez maintenant vous connecter.",
        )
    )
    db.session.commit()
    return jsonify(user.to_dict())


@admin_bp.post("/accounts/<user_id>/refuse")
@role_required("admin")
def refuse_account(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Compte introuvable."}), 404

    data = request.get_json(silent=True) or {}
    user.statut = AccountStatusEnum.REFUSE

    message = "Votre inscription a été refusée."
    if data.get("motif"):
        message += f" Motif : {data['motif']}"

    db.session.add(Notification(user_id=user.id, titre="Inscription refusée", message=message))
    db.session.commit()
    return jsonify(user.to_dict())


@admin_bp.post("/accounts/<user_id>/request-document")
@role_required("admin")
def request_document(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Compte introuvable."}), 404

    data = request.get_json(silent=True) or {}
    user.statut = AccountStatusEnum.PIECE_A_FOURNIR

    message = "Une nouvelle pièce justificative est demandée pour valider votre compte."
    if data.get("motif"):
        message += f" {data['motif']}"

    db.session.add(
        Notification(user_id=user.id, titre="Pièce justificative demandée", message=message)
    )
    db.session.commit()
    return jsonify(user.to_dict())


# ---------- Structure académique : filières, options, années, classes ----------

@admin_bp.get("/programs")
@role_required("admin")
def admin_list_programs():
    items = Program.query.order_by(Program.nom).all()
    return jsonify({"items": [p.to_dict() for p in items]})


@admin_bp.post("/programs")
@role_required("admin")
def create_program():
    data = request.get_json(silent=True) or {}
    if not data.get("nom") or not data.get("code"):
        return jsonify({"message": "nom et code sont requis."}), 400

    if Program.query.filter_by(code=data["code"]).first():
        return jsonify({"message": "Ce code de filière existe déjà."}), 409

    program = Program(
        nom=data["nom"], code=data["code"], description=data.get("description")
    )
    db.session.add(program)
    db.session.commit()
    return jsonify(program.to_dict()), 201


@admin_bp.patch("/programs/<program_id>")
@role_required("admin")
def update_program(program_id):
    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Filière introuvable."}), 404

    data = request.get_json(silent=True) or {}
    for field in ("nom", "code", "description", "actif"):
        if field in data:
            setattr(program, field, data[field])

    db.session.commit()
    return jsonify(program.to_dict())


@admin_bp.get("/options")
@role_required("admin")
def admin_list_options():
    program_id = request.args.get("program_id")
    query = ProgramOption.query
    if program_id:
        query = query.filter_by(program_id=program_id)
    items = query.order_by(ProgramOption.nom).all()
    return jsonify({"items": [o.to_dict() for o in items]})


@admin_bp.post("/options")
@role_required("admin")
def create_option():
    data = request.get_json(silent=True) or {}
    required = ["nom", "code", "program_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if not Program.query.get(data["program_id"]):
        return jsonify({"message": "Filière introuvable."}), 404

    existing = ProgramOption.query.filter_by(
        program_id=data["program_id"], code=data["code"]
    ).first()
    if existing:
        return jsonify({"message": "Ce code d'option existe déjà pour cette filière."}), 409

    option = ProgramOption(
        nom=data["nom"], code=data["code"], program_id=data["program_id"]
    )
    db.session.add(option)
    db.session.commit()
    return jsonify(option.to_dict()), 201


@admin_bp.patch("/options/<option_id>")
@role_required("admin")
def update_option(option_id):
    option = ProgramOption.query.get(option_id)
    if not option:
        return jsonify({"message": "Option introuvable."}), 404

    data = request.get_json(silent=True) or {}
    for field in ("nom", "code", "actif"):
        if field in data:
            setattr(option, field, data[field])

    db.session.commit()
    return jsonify(option.to_dict())


@admin_bp.get("/study-years")
@role_required("admin")
def admin_list_study_years():
    items = StudyYear.query.order_by(StudyYear.niveau).all()
    return jsonify({"items": [y.to_dict() for y in items]})


@admin_bp.post("/study-years")
@role_required("admin")
def create_study_year():
    data = request.get_json(silent=True) or {}
    if not data.get("nom") or data.get("niveau") is None:
        return jsonify({"message": "nom et niveau sont requis."}), 400

    if StudyYear.query.filter_by(nom=data["nom"]).first():
        return jsonify({"message": "Cette année d'étude existe déjà."}), 409

    study_year = StudyYear(nom=data["nom"], niveau=data["niveau"])
    db.session.add(study_year)
    db.session.commit()
    return jsonify(study_year.to_dict()), 201


@admin_bp.get("/classes")
@role_required("admin")
def admin_list_classes():
    option_id = request.args.get("option_id")
    query = ClassGroup.query
    if option_id:
        query = query.filter_by(option_id=option_id)
    items = query.all()
    return jsonify({"items": [c.to_dict() for c in items]})


@admin_bp.post("/classes")
@role_required("admin")
def create_class():
    data = request.get_json(silent=True) or {}
    required = ["nom", "option_id", "study_year_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if not ProgramOption.query.get(data["option_id"]):
        return jsonify({"message": "Option introuvable."}), 404
    if not StudyYear.query.get(data["study_year_id"]):
        return jsonify({"message": "Année d'étude introuvable."}), 404

    classe = ClassGroup(
        nom=data["nom"],
        option_id=data["option_id"],
        study_year_id=data["study_year_id"],
    )
    db.session.add(classe)
    db.session.commit()
    return jsonify(classe.to_dict()), 201


@admin_bp.patch("/classes/<class_id>")
@role_required("admin")
def update_class(class_id):
    classe = ClassGroup.query.get(class_id)
    if not classe:
        return jsonify({"message": "Classe introuvable."}), 404

    data = request.get_json(silent=True) or {}
    for field in ("nom", "actif"):
        if field in data:
            setattr(classe, field, data[field])

    db.session.commit()
    return jsonify(classe.to_dict())


@admin_bp.get("/teachers")
@role_required("admin")
def list_teachers():
    """Enseignants validés, pour les affecter à des matières/classes."""
    teachers = (
        Teacher.query.join(User).filter(User.statut == AccountStatusEnum.VALIDE).all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": t.id,
                    "user_id": t.user_id,
                    "nom_complet": t.user.nom_complet,
                    "email": t.user.email,
                }
                for t in teachers
            ]
        }
    )


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


# ---------- Semestres ----------

@admin_bp.get("/semesters")
@role_required("admin")
def list_semesters():
    items = Semester.query.order_by(Semester.date_debut.desc()).all()
    return jsonify({"items": [s.to_dict() for s in items]})


@admin_bp.post("/semesters")
@role_required("admin")
def create_semester():
    data = request.get_json(silent=True) or {}
    required = ["nom", "annee_academique", "date_debut", "date_fin"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    try:
        date_debut = datetime.strptime(data["date_debut"], "%Y-%m-%d").date()
        date_fin = datetime.strptime(data["date_fin"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Dates invalides (format attendu : AAAA-MM-JJ)."}), 400

    if date_fin <= date_debut:
        return jsonify({"message": "La date de fin doit être après la date de début."}), 400

    existing = Semester.query.filter_by(
        nom=data["nom"], annee_academique=data["annee_academique"]
    ).first()
    if existing:
        return jsonify({"message": "Ce semestre existe déjà pour cette année académique."}), 409

    semester = Semester(
        nom=data["nom"],
        annee_academique=data["annee_academique"],
        date_debut=date_debut,
        date_fin=date_fin,
    )
    db.session.add(semester)
    db.session.commit()

    return jsonify(semester.to_dict()), 201


# ---------- Affectations enseignant (matière + classe + semestre) ----------

@admin_bp.get("/teacher-assignments")
@role_required("admin")
def list_teacher_assignments():
    teacher_id = request.args.get("teacher_id")
    semester_id = request.args.get("semester_id")

    query = TeacherAssignment.query
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if semester_id:
        query = query.filter_by(semester_id=semester_id)

    items = query.all()
    return jsonify({"items": [a.to_dict() for a in items]})


@admin_bp.post("/teacher-assignments")
@role_required("admin")
def create_teacher_assignment():
    """
    Affecte un enseignant à une matière, dans une classe, pour un semestre.
    Un enseignant peut avoir plusieurs affectations (plusieurs matières et/ou classes).
    """
    data = request.get_json(silent=True) or {}
    required = ["teacher_id", "classe_id", "subject_id", "semester_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    teacher = Teacher.query.get(data["teacher_id"])
    if not teacher:
        return jsonify({"message": "Enseignant introuvable."}), 404
    classe = ClassGroup.query.get(data["classe_id"])
    if not classe:
        return jsonify({"message": "Classe introuvable."}), 404
    subject = Subject.query.get(data["subject_id"])
    if not subject:
        return jsonify({"message": "Matière introuvable."}), 404
    semester = Semester.query.get(data["semester_id"])
    if not semester:
        return jsonify({"message": "Semestre introuvable."}), 404

    existing = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id,
        classe_id=classe.id,
        subject_id=subject.id,
        semester_id=semester.id,
    ).first()
    if existing:
        return jsonify({"message": "Cette affectation existe déjà."}), 409

    assignment = TeacherAssignment(
        teacher_id=teacher.id,
        classe_id=classe.id,
        subject_id=subject.id,
        semester_id=semester.id,
    )
    db.session.add(assignment)

    db.session.add(
        Notification(
            user_id=teacher.user_id,
            titre="Nouvelle affectation",
            message=f"Vous avez été affecté à {subject.nom} — {classe.nom} pour {semester.nom} ({semester.annee_academique}).",
        )
    )

    db.session.commit()
    return jsonify(assignment.to_dict()), 201


@admin_bp.delete("/teacher-assignments/<assignment_id>")
@role_required("admin")
def delete_teacher_assignment(assignment_id):
    assignment = TeacherAssignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"message": "Affectation introuvable."}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Affectation retirée."})


# ---------- Emploi du temps (créneaux) ----------

@admin_bp.get("/schedule-slots")
@role_required("admin")
def list_schedule_slots():
    teacher_id = request.args.get("teacher_id")
    semester_id = request.args.get("semester_id")

    query = ScheduleSlot.query.join(TeacherAssignment)
    if teacher_id:
        query = query.filter(TeacherAssignment.teacher_id == teacher_id)
    if semester_id:
        query = query.filter(TeacherAssignment.semester_id == semester_id)

    items = query.all()
    return jsonify({"items": [s.to_dict() for s in items]})


@admin_bp.post("/schedule-slots")
@role_required("admin")
def create_schedule_slot():
    """
    Ajoute un créneau (jour + heure de début/fin + salle) à une affectation
    déjà décidée par l'administration. C'est la construction de l'emploi du
    temps de l'enseignant pour le semestre.
    """
    data = request.get_json(silent=True) or {}
    required = ["assignment_id", "jour_semaine", "heure_debut", "heure_fin"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if data["jour_semaine"] not in JOURS_SEMAINE:
        return (
            jsonify({"message": f"Jour invalide. Valeurs possibles : {', '.join(JOURS_SEMAINE)}"}),
            400,
        )

    assignment = TeacherAssignment.query.get(data["assignment_id"])
    if not assignment:
        return jsonify({"message": "Affectation introuvable."}), 404

    if data["heure_fin"] <= data["heure_debut"]:
        return jsonify({"message": "L'heure de fin doit être après l'heure de début."}), 400

    slot = ScheduleSlot(
        assignment_id=assignment.id,
        jour_semaine=data["jour_semaine"],
        heure_debut=data["heure_debut"],
        heure_fin=data["heure_fin"],
        salle=data.get("salle"),
    )
    db.session.add(slot)
    db.session.commit()

    return jsonify(slot.to_dict()), 201


@admin_bp.delete("/schedule-slots/<slot_id>")
@role_required("admin")
def delete_schedule_slot(slot_id):
    slot = ScheduleSlot.query.get(slot_id)
    if not slot:
        return jsonify({"message": "Créneau introuvable."}), 404

    db.session.delete(slot)
    db.session.commit()
    return jsonify({"message": "Créneau supprimé."})


@admin_bp.post("/schedule/publish")
@role_required("admin")
def publish_schedule():
    """
    Notifie un enseignant que son emploi du temps pour un semestre est prêt
    (à appeler une fois tous les créneaux saisis pour ce semestre).
    """
    data = request.get_json(silent=True) or {}
    teacher_id = data.get("teacher_id")
    semester_id = data.get("semester_id")
    if not teacher_id or not semester_id:
        return jsonify({"message": "teacher_id et semester_id sont requis."}), 400

    teacher = Teacher.query.get(teacher_id)
    semester = Semester.query.get(semester_id)
    if not teacher or not semester:
        return jsonify({"message": "Enseignant ou semestre introuvable."}), 404

    db.session.add(
        Notification(
            user_id=teacher.user_id,
            titre="Emploi du temps disponible",
            message=f"Votre emploi du temps pour {semester.nom} ({semester.annee_academique}) est disponible.",
        )
    )
    db.session.commit()

    return jsonify({"message": "Notification envoyée à l'enseignant."})


# ---------- Programmes annuels & documents administratifs ----------

DESTINATAIRE_TYPES = ["classe", "role_etudiant", "role_enseignant", "tous", "utilisateur"]


def _notify_academic_program(academic_program):
    titre = (
        "Nouveau programme annuel disponible"
        if "programme" in academic_program.titre.lower()
        else "Nouveau document administratif"
    )
    message = academic_program.titre

    if academic_program.destinataire_type == "classe":
        students = Student.query.filter_by(classe_id=academic_program.destinataire_id).all()
        for s in students:
            db.session.add(Notification(user_id=s.user_id, titre=titre, message=message))
    elif academic_program.destinataire_type == "role_etudiant":
        users = User.query.filter_by(role=RoleEnum.ETUDIANT, statut=AccountStatusEnum.VALIDE).all()
        for u in users:
            db.session.add(Notification(user_id=u.id, titre=titre, message=message))
    elif academic_program.destinataire_type == "role_enseignant":
        users = User.query.filter_by(role=RoleEnum.ENSEIGNANT, statut=AccountStatusEnum.VALIDE).all()
        for u in users:
            db.session.add(Notification(user_id=u.id, titre=titre, message=message))
    elif academic_program.destinataire_type == "tous":
        users = User.query.filter(
            User.role != RoleEnum.ADMIN, User.statut == AccountStatusEnum.VALIDE
        ).all()
        for u in users:
            db.session.add(Notification(user_id=u.id, titre=titre, message=message))
    elif academic_program.destinataire_type == "utilisateur":
        db.session.add(
            Notification(user_id=academic_program.destinataire_id, titre=titre, message=message)
        )


@admin_bp.get("/academic-programs")
@role_required("admin")
def list_academic_programs():
    items = AcademicProgram.query.order_by(AcademicProgram.date_publication.desc()).all()
    return jsonify({"items": [a.to_dict() for a in items]})


@admin_bp.post("/academic-programs")
@role_required("admin")
def create_academic_program():
    """
    Envoi d'un document administratif (programme annuel, calendrier, note de
    service, règlement...) à une classe, un rôle entier, tout le monde, ou un
    utilisateur précis.
    """
    form = request.form
    required = ["titre", "destinataire_type"]
    missing = [f for f in required if not form.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if form["destinataire_type"] not in DESTINATAIRE_TYPES:
        return (
            jsonify(
                {
                    "message": f"destinataire_type invalide. Valeurs possibles : {', '.join(DESTINATAIRE_TYPES)}"
                }
            ),
            400,
        )

    needs_target = form["destinataire_type"] in ("classe", "utilisateur")
    if needs_target and not form.get("destinataire_id"):
        return jsonify({"message": "destinataire_id est requis pour ce type de destinataire."}), 400

    fichier = request.files.get("fichier")
    if not fichier or fichier.filename == "":
        return jsonify({"message": "Le fichier est obligatoire."}), 400
    if not _allowed_upload(fichier.filename):
        return jsonify({"message": "Format de fichier non autorisé."}), 400

    upload_dir = current_app.config["UPLOAD_FOLDER"] + "/programmes"
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"{datetime.utcnow().timestamp()}_{fichier.filename}")
    fichier.save(os.path.join(upload_dir, filename))

    academic_program = AcademicProgram(
        titre=form["titre"],
        fichier=filename,
        annee_academique=form.get("annee_academique"),
        destinataire_type=form["destinataire_type"],
        destinataire_id=form.get("destinataire_id"),
    )
    db.session.add(academic_program)
    db.session.flush()

    _notify_academic_program(academic_program)

    db.session.commit()
    return jsonify(academic_program.to_dict()), 201


@admin_bp.get("/academic-programs/<filename>/download")
@role_required("admin")
def download_academic_program(filename):
    upload_dir = current_app.config["UPLOAD_FOLDER"] + "/programmes"
    return send_from_directory(upload_dir, filename)


def _allowed_upload(filename):
    allowed = current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ---------- Examens (calendrier global) ----------

@admin_bp.get("/exams")
@role_required("admin")
def list_exams_admin():
    classe_id = request.args.get("classe_id")
    query = Exam.query
    if classe_id:
        query = query.filter_by(classe_id=classe_id)

    exams = query.order_by(Exam.date, Exam.heure).all()

    # Détection de conflit : même date + même salle + même créneau horaire,
    # pour deux classes différentes.
    by_slot = {}
    for e in exams:
        if not e.salle:
            continue
        key = (e.date, e.heure, e.salle)
        by_slot.setdefault(key, []).append(e.id)

    conflicting_ids = {
        eid for ids in by_slot.values() if len(ids) > 1 for eid in ids
    }

    items = []
    for e in exams:
        data = e.to_dict()
        data["conflit_salle"] = e.id in conflicting_ids
        items.append(data)

    return jsonify({"items": items})


@admin_bp.post("/exams")
@role_required("admin")
def create_exam_admin():
    """L'administration peut aussi publier directement un examen pour une classe."""
    data = request.get_json(silent=True) or {}
    required = ["titre", "classe_id", "subject_id", "date", "heure"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    classe = ClassGroup.query.get(data["classe_id"])
    if not classe:
        return jsonify({"message": "Classe introuvable."}), 404
    if not Subject.query.get(data["subject_id"]):
        return jsonify({"message": "Matière introuvable."}), 404

    try:
        exam_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Date invalide (format attendu : AAAA-MM-JJ)."}), 400

    exam = Exam(
        titre=data["titre"],
        classe_id=data["classe_id"],
        matiere_id=data["subject_id"],
        date=exam_date,
        heure=data["heure"],
        salle=data.get("salle"),
    )
    db.session.add(exam)
    db.session.flush()

    students = Student.query.filter_by(classe_id=classe.id).all()
    for s in students:
        db.session.add(
            Notification(
                user_id=s.user_id,
                titre="Nouvel examen",
                message=f"{exam.titre} — le {data['date']} à {data['heure']}"
                + (f", salle {data.get('salle')}" if data.get("salle") else ""),
            )
        )

    db.session.commit()
    return jsonify(exam.to_dict()), 201


@admin_bp.patch("/exams/<exam_id>")
@role_required("admin")
def update_exam_admin(exam_id):
    exam = Exam.query.get(exam_id)
    if not exam:
        return jsonify({"message": "Examen introuvable."}), 404

    data = request.get_json(silent=True) or {}
    if "titre" in data:
        exam.titre = data["titre"]
    if "date" in data:
        try:
            exam.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Date invalide (format attendu : AAAA-MM-JJ)."}), 400
    if "heure" in data:
        exam.heure = data["heure"]
    if "salle" in data:
        exam.salle = data["salle"]

    db.session.commit()
    return jsonify(exam.to_dict())


@admin_bp.delete("/exams/<exam_id>")
@role_required("admin")
def delete_exam_admin(exam_id):
    exam = Exam.query.get(exam_id)
    if not exam:
        return jsonify({"message": "Examen introuvable."}), 404

    db.session.delete(exam)
    db.session.commit()
    return jsonify({"message": "Examen supprimé."})


# ---------- Recherche d'étudiants & messagerie ciblée ----------

@admin_bp.get("/students/search")
@role_required("admin")
def search_students():
    """Recherche d'étudiants par nom, avec filière/option/année affichées."""
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify({"items": []})

    students = (
        Student.query.join(User)
        .filter(User.nom_complet.ilike(f"%{q}%"), User.statut == AccountStatusEnum.VALIDE)
        .limit(20)
        .all()
    )

    items = []
    for s in students:
        if not s.classe:
            continue
        items.append(
            {
                "student_id": s.id,
                "user_id": s.user_id,
                "nom_complet": s.user.nom_complet,
                "filiere": s.classe.option.program.nom if s.classe.option else None,
                "option": s.classe.option.nom if s.classe.option else None,
                "annee_etude": s.classe.study_year.nom if s.classe.study_year else None,
                "classe": s.classe.nom,
            }
        )
    return jsonify({"items": items})


@admin_bp.post("/messages")
@role_required("admin")
def send_message():
    """Envoie un message (notification) à un ou plusieurs étudiants sélectionnés."""
    data = request.get_json(silent=True) or {}
    required = ["user_ids", "titre", "message"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if not isinstance(data["user_ids"], list) or not data["user_ids"]:
        return jsonify({"message": "Sélectionnez au moins un destinataire."}), 400

    count = 0
    for user_id in data["user_ids"]:
        if User.query.get(user_id):
            db.session.add(
                Notification(user_id=user_id, titre=data["titre"], message=data["message"])
            )
            count += 1

    db.session.commit()
    return jsonify({"message": f"Message envoyé à {count} destinataire(s)."})


# ---------- Notes (consultation & gestion) ----------

@admin_bp.get("/grades")
@role_required("admin")
def list_grades_admin():
    classe_id = request.args.get("classe_id")
    subject_id = request.args.get("subject_id")

    query = Grade.query
    if classe_id:
        query = query.filter_by(classe_id=classe_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    items = query.all()
    return jsonify({"items": [g.to_dict() for g in items]})


@admin_bp.patch("/grades/<grade_id>")
@role_required("admin")
def update_grade_admin(grade_id):
    grade = Grade.query.get(grade_id)
    if not grade:
        return jsonify({"message": "Note introuvable."}), 404

    data = request.get_json(silent=True) or {}
    if "valeur" in data:
        grade.valeur = data["valeur"]

    db.session.commit()
    return jsonify(grade.to_dict())


@admin_bp.delete("/grades/<grade_id>")
@role_required("admin")
def delete_grade_admin(grade_id):
    grade = Grade.query.get(grade_id)
    if not grade:
        return jsonify({"message": "Note introuvable."}), 404

    db.session.delete(grade)
    db.session.commit()
    return jsonify({"message": "Note supprimée."})