import enum
from datetime import datetime

from app.extensions import db
from app.models.user import gen_uuid


class GradeTypeEnum(str, enum.Enum):
    INTERROGATION = "interrogation"
    SESSION = "session"
    RATTRAPAGE = "rattrapage"


class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.String(36), db.ForeignKey("subjects.id"), nullable=False)
    classe_id = db.Column(db.String(36), db.ForeignKey("classes.id"), nullable=False)
    semester_id = db.Column(db.String(36), db.ForeignKey("semesters.id"), nullable=True)
    teacher_id = db.Column(db.String(36), db.ForeignKey("teachers.id"), nullable=True)

    type = db.Column(db.Enum(GradeTypeEnum), nullable=False)
    valeur = db.Column(db.Float, nullable=False)
    bareme = db.Column(db.Float, default=20)
    date_saisie = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    subject = db.relationship("Subject")
    classe = db.relationship("ClassGroup")
    semester = db.relationship("Semester")
    teacher = db.relationship("Teacher")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject_id", "type", "semester_id",
            name="uq_grade_unique_entry",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "etudiant": self.student.user.nom_complet if self.student and self.student.user else None,
            "subject_id": self.subject_id,
            "matiere": self.subject.nom if self.subject else None,
            "classe_id": self.classe_id,
            "classe": self.classe.nom if self.classe else None,
            "semester_id": self.semester_id,
            "semestre": self.semester.nom if self.semester else None,
            "type": self.type.value if self.type else None,
            "valeur": self.valeur,
            "bareme": self.bareme,
            "date_saisie": self.date_saisie.isoformat() if self.date_saisie else None,
        }