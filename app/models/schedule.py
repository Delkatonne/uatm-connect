from datetime import datetime

from app.extensions import db
from app.models.user import gen_uuid

JOURS_SEMAINE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]


class Semester(db.Model):
    """Semestre défini par l'administration (ex: Semestre 1 — 2025-2026)."""

    __tablename__ = "semesters"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(100), nullable=False)  # ex: "Semestre 1"
    annee_academique = db.Column(db.String(9), nullable=False)  # ex: "2025-2026"
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    actif = db.Column(db.Boolean, default=True)

    assignments = db.relationship(
        "TeacherAssignment", back_populates="semester", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "nom", "annee_academique", name="uq_semester_nom_annee"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "annee_academique": self.annee_academique,
            "date_debut": self.date_debut.isoformat() if self.date_debut else None,
            "date_fin": self.date_fin.isoformat() if self.date_fin else None,
            "actif": self.actif,
        }


class TeacherAssignment(db.Model):
    """
    Décision de l'administration : cet enseignant prend en charge cette matière
    dans cette classe, pour ce semestre. Un enseignant peut avoir plusieurs
    matières et plusieurs classes (donc plusieurs lignes).
    """

    __tablename__ = "teacher_assignments"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    teacher_id = db.Column(db.String(36), db.ForeignKey("teachers.id"), nullable=False)
    classe_id = db.Column(db.String(36), db.ForeignKey("classes.id"), nullable=False)
    subject_id = db.Column(db.String(36), db.ForeignKey("subjects.id"), nullable=False)
    semester_id = db.Column(db.String(36), db.ForeignKey("semesters.id"), nullable=False)
    date_affectation = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("Teacher", back_populates="assignments")
    classe = db.relationship("ClassGroup", back_populates="teacher_assignments")
    subject = db.relationship("Subject")
    semester = db.relationship("Semester", back_populates="assignments")
    schedule_slots = db.relationship(
        "ScheduleSlot", back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "teacher_id",
            "classe_id",
            "subject_id",
            "semester_id",
            name="uq_assignment_unique",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "enseignant": self.teacher.user.nom_complet if self.teacher and self.teacher.user else None,
            "classe_id": self.classe_id,
            "classe": self.classe.nom if self.classe else None,
            "subject_id": self.subject_id,
            "matiere": self.subject.nom if self.subject else None,
            "semester_id": self.semester_id,
            "semestre": self.semester.nom if self.semester else None,
            "annee_academique": self.semester.annee_academique if self.semester else None,
        }


class ScheduleSlot(db.Model):
    """
    Créneau d'emploi du temps que l'administration fixe pour une affectation
    (jour, plage horaire, salle). L'ensemble des créneaux d'un enseignant sur
    un semestre constitue son emploi du temps.
    """

    __tablename__ = "schedule_slots"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    assignment_id = db.Column(
        db.String(36), db.ForeignKey("teacher_assignments.id"), nullable=False
    )
    jour_semaine = db.Column(db.String(15), nullable=False)  # lundi, mardi, ...
    heure_debut = db.Column(db.String(5), nullable=False)  # "08:00"
    heure_fin = db.Column(db.String(5), nullable=False)  # "10:00"
    salle = db.Column(db.String(100), nullable=True)

    assignment = db.relationship("TeacherAssignment", back_populates="schedule_slots")

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "jour_semaine": self.jour_semaine,
            "heure_debut": self.heure_debut,
            "heure_fin": self.heure_fin,
            "salle": self.salle,
            "matiere": self.assignment.subject.nom if self.assignment and self.assignment.subject else None,
            "classe": self.assignment.classe.nom if self.assignment and self.assignment.classe else None,
        }