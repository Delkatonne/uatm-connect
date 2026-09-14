from datetime import datetime

from app.extensions import db
from app.models.user import gen_uuid


class Absence(db.Model):
    __tablename__ = "absences"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.String(36), db.ForeignKey("subjects.id"), nullable=False)
    classe_id = db.Column(db.String(36), db.ForeignKey("classes.id"), nullable=False)
    teacher_id = db.Column(db.String(36), db.ForeignKey("teachers.id"), nullable=True)

    date = db.Column(db.Date, nullable=False)
    justifiee = db.Column(db.Boolean, default=False)
    motif = db.Column(db.Text, nullable=True)
    date_saisie = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    subject = db.relationship("Subject")
    classe = db.relationship("ClassGroup")
    teacher = db.relationship("Teacher")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject_id", "date", name="uq_absence_unique_entry"
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
            "date": self.date.isoformat() if self.date else None,
            "justifiee": self.justifiee,
            "motif": self.motif,
            "date_saisie": self.date_saisie.isoformat() if self.date_saisie else None,
        }