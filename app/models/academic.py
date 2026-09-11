from datetime import datetime

from app.extensions import db
from app.models.user import gen_uuid


class Program(db.Model):
    """Filière (ex: Génie Électrique)."""

    __tablename__ = "programs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    actif = db.Column(db.Boolean, default=True)

    options = db.relationship(
        "ProgramOption", back_populates="program", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "code": self.code,
            "description": self.description,
            "actif": self.actif,
        }


class ProgramOption(db.Model):
    """Option / spécialité (ex: SIL), rattachée à une filière."""

    __tablename__ = "options"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    program_id = db.Column(db.String(36), db.ForeignKey("programs.id"), nullable=False)
    actif = db.Column(db.Boolean, default=True)

    program = db.relationship("Program", back_populates="options")
    classes = db.relationship(
        "ClassGroup", back_populates="option", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("program_id", "code", name="uq_option_code_per_program"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "code": self.code,
            "program_id": self.program_id,
            "actif": self.actif,
        }


class StudyYear(db.Model):
    """Année d'étude (1ère année, Master 1, etc.)."""

    __tablename__ = "study_years"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(50), nullable=False, unique=True)
    niveau = db.Column(db.Integer, nullable=False)  # ordre d'affichage/tri

    def to_dict(self):
        return {"id": self.id, "nom": self.nom, "niveau": self.niveau}


class ClassGroup(db.Model):
    """Classe (ex: SIL 3) = option + année d'étude."""

    __tablename__ = "classes"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(100), nullable=False)
    option_id = db.Column(db.String(36), db.ForeignKey("options.id"), nullable=False)
    study_year_id = db.Column(
        db.String(36), db.ForeignKey("study_years.id"), nullable=False
    )
    actif = db.Column(db.Boolean, default=True)

    option = db.relationship("ProgramOption", back_populates="classes")
    study_year = db.relationship("StudyYear")
    students = db.relationship("Student", back_populates="classe")
    teacher_links = db.relationship(
        "TeacherClass", back_populates="classe", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "option_id": self.option_id,
            "study_year_id": self.study_year_id,
            "filiere": self.option.program.nom if self.option else None,
            "option": self.option.nom if self.option else None,
            "annee_etude": self.study_year.nom if self.study_year else None,
            "actif": self.actif,
        }

    def matieres(self):
        """Matières applicables à cette classe : celles des UE de sa filière + son année."""
        if not self.option:
            return []
        ue_ids = [
            ue.id
            for ue in TeachingUnit.query.filter_by(
                program_id=self.option.program_id,
                study_year_id=self.study_year_id,
            ).all()
        ]
        if not ue_ids:
            return []
        return Subject.query.filter(Subject.ue_id.in_(ue_ids)).all()


class TeachingUnit(db.Model):
    """UE (Unité d'Enseignement) : regroupe des matières pour une filière + une année d'étude."""

    __tablename__ = "teaching_units"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), nullable=True)
    program_id = db.Column(db.String(36), db.ForeignKey("programs.id"), nullable=False)
    study_year_id = db.Column(
        db.String(36), db.ForeignKey("study_years.id"), nullable=False
    )
    actif = db.Column(db.Boolean, default=True)

    program = db.relationship("Program")
    study_year = db.relationship("StudyYear")
    subjects = db.relationship(
        "Subject", back_populates="teaching_unit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "program_id", "study_year_id", "nom", name="uq_ue_per_program_year"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "code": self.code,
            "program_id": self.program_id,
            "filiere": self.program.nom if self.program else None,
            "study_year_id": self.study_year_id,
            "annee_etude": self.study_year.nom if self.study_year else None,
            "actif": self.actif,
        }


class Subject(db.Model):
    """Matière, rattachée à une UE (elle-même liée à filière + année)."""

    __tablename__ = "subjects"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom = db.Column(db.String(150), nullable=False)
    ue_id = db.Column(db.String(36), db.ForeignKey("teaching_units.id"), nullable=False)

    teaching_unit = db.relationship("TeachingUnit", back_populates="subjects")

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "ue_id": self.ue_id,
            "ue": self.teaching_unit.nom if self.teaching_unit else None,
            "filiere": self.teaching_unit.program.nom
            if self.teaching_unit and self.teaching_unit.program
            else None,
            "annee_etude": self.teaching_unit.study_year.nom
            if self.teaching_unit and self.teaching_unit.study_year
            else None,
        }


class TeacherClass(db.Model):
    """Affectation enseignant <-> classe (dernier mot à l'administration)."""

    __tablename__ = "teacher_classes"

    teacher_id = db.Column(
        db.String(36), db.ForeignKey("teachers.id"), primary_key=True
    )
    class_id = db.Column(db.String(36), db.ForeignKey("classes.id"), primary_key=True)
    date_affectation = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("Teacher", back_populates="class_links")
    classe = db.relationship("ClassGroup", back_populates="teacher_links")


class TeacherSubject(db.Model):
    """Affectation enseignant <-> matière."""

    __tablename__ = "teacher_subjects"

    teacher_id = db.Column(
        db.String(36), db.ForeignKey("teachers.id"), primary_key=True
    )
    subject_id = db.Column(
        db.String(36), db.ForeignKey("subjects.id"), primary_key=True
    )

    teacher = db.relationship("Teacher", back_populates="subject_links")
    subject = db.relationship("Subject")