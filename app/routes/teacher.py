import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    Teacher,
    TeacherAssignment,
    ScheduleSlot,
    Document,
    Exam,
    Notification,
    Student,
    DOCUMENT_TYPES,
    AcademicProgram,
    Grade,
    GradeTypeEnum,
    Absence,
)
from app.utils.decorators import account_must_be_valide, role_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/api/teacher")


def _current_teacher():
    user_id = get_jwt_identity()
    return Teacher.query.filter_by(user_id=user_id).first()


def _has_assignment(teacher_id, classe_id, subject_id):
    return (
        TeacherAssignment.query.filter_by(
            teacher_id=teacher_id, classe_id=classe_id, subject_id=subject_id
        ).first()
        is not None
    )


def _notify_class(classe_id, titre, message):
    students = Student.query.filter_by(classe_id=classe_id).all()
    for student in students:
        db.session.add(Notification(user_id=student.user_id, titre=titre, message=message))


@teacher_bp.get("/me")
@role_required("enseignant")
@account_must_be_valide
def me():
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"message": "Profil enseignant introuvable."}), 404

    return jsonify(
        {
            "nom_complet": teacher.user.nom_complet,
            "email": teacher.user.email,
            "telephone": teacher.user.telephone,
            "photo_profil": teacher.user.photo_profil,
            "departement": teacher.departement,
            "fonction": teacher.fonction,
            "matieres_declarees": teacher.matieres_declarees,
        }
    )


@teacher_bp.patch("/me")
@role_required("enseignant")
@account_must_be_valide
def update_me():
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"message": "Profil enseignant introuvable."}), 404

    if request.content_type and "multipart/form-data" in request.content_type:
        telephone = request.form.get("telephone")
        photo = request.files.get("photo")
        if telephone:
            teacher.user.telephone = telephone
        if photo and photo.filename:
            if not _allowed_image(photo.filename):
                return jsonify({"message": "Format de photo non autorisé."}), 400
            upload_dir = current_app.config["UPLOAD_FOLDER"] + "/photos"
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"{teacher.user.id}_{photo.filename}")
            photo.save(os.path.join(upload_dir, filename))
            teacher.user.photo_profil = filename
    else:
        data = request.get_json(silent=True) or {}
        if "telephone" in data:
            teacher.user.telephone = data["telephone"]

    db.session.commit()
    return jsonify({"message": "Profil mis à jour."})


def _allowed_image(filename):
    allowed = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@teacher_bp.get("/assignments")
@role_required("enseignant")
@account_must_be_valide
def assignments():
    """Mes matières et mes classes (éventuellement filtrées par semestre)."""
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    semester_id = request.args.get("semester_id")
    query = TeacherAssignment.query.filter_by(teacher_id=teacher.id)
    if semester_id:
        query = query.filter_by(semester_id=semester_id)

    items = query.all()
    return jsonify({"items": [a.to_dict() for a in items]})


@teacher_bp.get("/schedule")
@role_required("enseignant")
@account_must_be_valide
def schedule():
    """Mon emploi du temps pour un semestre donné (envoyé par l'administration)."""
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    semester_id = request.args.get("semester_id")
    if not semester_id:
        return jsonify({"message": "semester_id est requis."}), 400

    slots = (
        ScheduleSlot.query.join(TeacherAssignment)
        .filter(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.semester_id == semester_id,
        )
        .all()
    )
    return jsonify({"items": [s.to_dict() for s in slots]})


@teacher_bp.get("/classes")
@role_required("enseignant")
@account_must_be_valide
def my_classes():
    """Mes classes (dédupliquées, toutes affectations confondues)."""
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
    classes = {a.classe.id: a.classe.to_dict() for a in assignments if a.classe}
    return jsonify({"items": list(classes.values())})


@teacher_bp.get("/subjects")
@role_required("enseignant")
@account_must_be_valide
def my_subjects():
    """Mes matières (dédupliquées)."""
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
    subjects = {a.subject.id: a.subject.to_dict() for a in assignments if a.subject}
    return jsonify({"items": list(subjects.values())})


@teacher_bp.get("/documents")
@role_required("enseignant")
@account_must_be_valide
def my_documents():
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    items = (
        Document.query.filter_by(teacher_id=teacher.id)
        .order_by(Document.date_publication.desc())
        .all()
    )
    return jsonify({"items": [d.to_dict() for d in items]})


@teacher_bp.post("/documents")
@role_required("enseignant")
@account_must_be_valide
def publish_document():
    """
    Publie un document (cours, exercice, devoir, TD, correction, examen,
    complémentaire) pour une classe. Tous les étudiants de cette classe
    le reçoivent automatiquement (notification), sans envoi individuel.
    """
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"message": "Profil enseignant introuvable."}), 404

    form = request.form
    required = ["titre", "type", "classe_id", "subject_id"]
    missing = [f for f in required if not form.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if form["type"] not in DOCUMENT_TYPES:
        return jsonify({"message": f"Type invalide. Valeurs possibles : {', '.join(DOCUMENT_TYPES)}"}), 400

    if not _has_assignment(teacher.id, form["classe_id"], form["subject_id"]):
        return (
            jsonify({"message": "Vous n'êtes pas affecté à cette matière pour cette classe."}),
            403,
        )

    fichier = request.files.get("fichier")
    if not fichier or fichier.filename == "":
        return jsonify({"message": "Le fichier est obligatoire."}), 400
    if not _allowed_file(fichier.filename, current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"]):
        return jsonify({"message": "Format de fichier non autorisé."}), 400

    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "documents")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"{teacher.id}_{datetime.utcnow().timestamp()}_{fichier.filename}")
    fichier.save(os.path.join(upload_dir, filename))

    document = Document(
        titre=form["titre"],
        description=form.get("description"),
        fichier=filename,
        type=form["type"],
        teacher_id=teacher.id,
        class_id=form["classe_id"],
        subject_id=form["subject_id"],
    )
    db.session.add(document)
    db.session.flush()

    _notify_class(
        form["classe_id"],
        f"Nouveau document — {document.type}",
        f"{teacher.user.nom_complet} a publié « {document.titre} ».",
    )

    db.session.commit()
    return jsonify(document.to_dict()), 201


def _allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@teacher_bp.get("/exams")
@role_required("enseignant")
@account_must_be_valide
def my_exams():
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    assignments = TeacherAssignment.query.filter_by(teacher_id=teacher.id).all()
    class_ids = {a.classe_id for a in assignments}
    if not class_ids:
        return jsonify({"items": []})

    items = Exam.query.filter(Exam.classe_id.in_(class_ids)).order_by(Exam.date).all()
    return jsonify({"items": [e.to_dict() for e in items]})


@teacher_bp.post("/exams")
@role_required("enseignant")
@account_must_be_valide
def publish_exam():
    """Publie les informations d'un examen (date, heure, salle) pour une classe."""
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"message": "Profil enseignant introuvable."}), 404

    data = request.get_json(silent=True) or {}
    required = ["titre", "classe_id", "subject_id", "date", "heure"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if not _has_assignment(teacher.id, data["classe_id"], data["subject_id"]):
        return (
            jsonify({"message": "Vous n'êtes pas affecté à cette matière pour cette classe."}),
            403,
        )

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

    _notify_class(
        data["classe_id"],
        "Nouvel examen",
        f"{exam.titre} — le {data['date']} à {data['heure']}" + (f", salle {data.get('salle')}" if data.get("salle") else ""),
    )

    db.session.commit()
    return jsonify(exam.to_dict()), 201


@teacher_bp.patch("/notifications/<notif_id>/read")
@role_required("enseignant")
@account_must_be_valide
def mark_notification_read(notif_id):
    user_id = get_jwt_identity()
    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if not notif:
        return jsonify({"message": "Notification introuvable."}), 404

    notif.lu = True
    db.session.commit()
    return jsonify(notif.to_dict())


@teacher_bp.get("/notifications")
@role_required("enseignant")
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


@teacher_bp.get("/academic-programs")
@role_required("enseignant")
@account_must_be_valide
def academic_programs():
    """Programmes annuels, calendriers, notes de service reçus de l'administration."""
    user_id = get_jwt_identity()
    items = AcademicProgram.query.filter(
        db.or_(
            AcademicProgram.destinataire_type == "role_enseignant",
            AcademicProgram.destinataire_type == "tous",
            db.and_(
                AcademicProgram.destinataire_type == "utilisateur",
                AcademicProgram.destinataire_id == user_id,
            ),
        )
    ).order_by(AcademicProgram.date_publication.desc()).all()

    return jsonify({"items": [a.to_dict() for a in items]})


# ---------- Notes ----------

GRADE_TYPES = [t.value for t in GradeTypeEnum]


@teacher_bp.get("/classes/<classe_id>/students")
@role_required("enseignant")
@account_must_be_valide
def class_students(classe_id):
    """Liste des étudiants d'une classe qui m'est attribuée, pour la saisie des notes."""
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    has_class = TeacherAssignment.query.filter_by(
        teacher_id=teacher.id, classe_id=classe_id
    ).first()
    if not has_class:
        return jsonify({"message": "Cette classe ne vous est pas attribuée."}), 403

    students = Student.query.filter_by(classe_id=classe_id).all()
    return jsonify(
        {
            "items": [
                {"student_id": s.id, "nom_complet": s.user.nom_complet}
                for s in students
                if s.user
            ]
        }
    )


@teacher_bp.get("/grades")
@role_required("enseignant")
@account_must_be_valide
def list_grades():
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    classe_id = request.args.get("classe_id")
    subject_id = request.args.get("subject_id")

    query = Grade.query.filter_by(teacher_id=teacher.id)
    if classe_id:
        query = query.filter_by(classe_id=classe_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    items = query.all()
    return jsonify({"items": [g.to_dict() for g in items]})


@teacher_bp.post("/grades")
@role_required("enseignant")
@account_must_be_valide
def submit_grades():
    """
    Saisie groupée des notes pour une classe/matière/type d'évaluation.
    Corps attendu :
      { classe_id, subject_id, semester_id, type,
        entries: [{ student_id, valeur }, ...] }
    """
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"message": "Profil enseignant introuvable."}), 404

    data = request.get_json(silent=True) or {}
    required = ["classe_id", "subject_id", "type", "entries"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if data["type"] not in GRADE_TYPES:
        return jsonify({"message": f"Type invalide. Valeurs possibles : {', '.join(GRADE_TYPES)}"}), 400

    if not _has_assignment(teacher.id, data["classe_id"], data["subject_id"]):
        return (
            jsonify({"message": "Vous n'êtes pas affecté à cette matière pour cette classe."}),
            403,
        )

    saved = []
    for entry in data["entries"]:
        student_id = entry.get("student_id")
        valeur = entry.get("valeur")
        if student_id is None or valeur is None:
            continue

        grade = Grade.query.filter_by(
            student_id=student_id,
            subject_id=data["subject_id"],
            type=data["type"],
            semester_id=data.get("semester_id"),
        ).first()

        if grade:
            grade.valeur = valeur
        else:
            grade = Grade(
                student_id=student_id,
                subject_id=data["subject_id"],
                classe_id=data["classe_id"],
                semester_id=data.get("semester_id"),
                teacher_id=teacher.id,
                type=data["type"],
                valeur=valeur,
                bareme=entry.get("bareme", 20),
            )
            db.session.add(grade)
        saved.append(grade)

    db.session.flush()

    student = Student.query.get(data["entries"][0].get("student_id")) if data["entries"] else None
    subject_nom = saved[0].subject.nom if saved and saved[0].subject else "une matière"

    for grade in saved:
        if grade.student and grade.student.user_id:
            db.session.add(
                Notification(
                    user_id=grade.student.user_id,
                    titre="Nouvelle note disponible",
                    message=f"Votre note de {grade.type.value} en {subject_nom} est disponible.",
                )
            )

    db.session.commit()
    return jsonify({"items": [g.to_dict() for g in saved]}), 201


# ---------- Absences ----------

@teacher_bp.get("/absences")
@role_required("enseignant")
@account_must_be_valide
def list_absences():
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"items": []})

    classe_id = request.args.get("classe_id")
    subject_id = request.args.get("subject_id")

    query = Absence.query.filter_by(teacher_id=teacher.id)
    if classe_id:
        query = query.filter_by(classe_id=classe_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    items = query.order_by(Absence.date.desc()).all()
    return jsonify({"items": [a.to_dict() for a in items]})


@teacher_bp.post("/absences")
@role_required("enseignant")
@account_must_be_valide
def submit_absences():
    """
    Saisie groupée des absences pour une classe/matière/date.
    Corps attendu : { classe_id, subject_id, date, student_ids: [...] }
    Seuls les étudiants listés dans student_ids sont marqués absents.
    """
    teacher = _current_teacher()
    if not teacher:
        return jsonify({"message": "Profil enseignant introuvable."}), 404

    data = request.get_json(silent=True) or {}
    required = ["classe_id", "subject_id", "date", "student_ids"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"message": f"Champs manquants : {', '.join(missing)}"}), 400

    if not _has_assignment(teacher.id, data["classe_id"], data["subject_id"]):
        return (
            jsonify({"message": "Vous n'êtes pas affecté à cette matière pour cette classe."}),
            403,
        )

    try:
        absence_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Date invalide (format attendu : AAAA-MM-JJ)."}), 400

    saved = []
    for student_id in data["student_ids"]:
        existing = Absence.query.filter_by(
            student_id=student_id, subject_id=data["subject_id"], date=absence_date
        ).first()
        if existing:
            saved.append(existing)
            continue

        absence = Absence(
            student_id=student_id,
            subject_id=data["subject_id"],
            classe_id=data["classe_id"],
            teacher_id=teacher.id,
            date=absence_date,
        )
        db.session.add(absence)
        saved.append(absence)

    db.session.flush()

    subject_nom = saved[0].subject.nom if saved and saved[0].subject else "un cours"
    for absence in saved:
        if absence.student and absence.student.user_id:
            db.session.add(
                Notification(
                    user_id=absence.student.user_id,
                    titre="Absence enregistrée",
                    message=f"Une absence a été enregistrée en {subject_nom} le {data['date']}.",
                )
            )

    db.session.commit()
    return jsonify({"items": [a.to_dict() for a in saved]}), 201