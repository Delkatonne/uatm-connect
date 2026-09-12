from datetime import datetime

from app.extensions import db
from app.models.user import gen_uuid


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)
    annee_inscription = db.Column(db.String(9), nullable=False)  # ex: "2025-2026"
    classe_id = db.Column(db.String(36), db.ForeignKey("classes.id"), nullable=True)

    user = db.relationship("User", back_populates="student_profile")
    classe = db.relationship("ClassGroup", back_populates="students")

    def to_dict(self):
        return {
            "id": self.id,
            "annee_inscription": self.annee_inscription,
            "classe": self.classe.to_dict() if self.classe else None,
        }


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)
    departement = db.Column(db.String(150), nullable=True)
    fonction = db.Column(db.String(150), nullable=True)
    matieres_declarees = db.Column(db.Text, nullable=True)  # saisies à l'inscription, à valider par l'admin

    user = db.relationship("User", back_populates="teacher_profile")
    assignments = db.relationship(
        "TeacherAssignment", back_populates="teacher", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "departement": self.departement,
            "fonction": self.fonction,
            "matieres_declarees": self.matieres_declarees,
            "classes": list(
                {a.classe.id: a.classe.to_dict() for a in self.assignments if a.classe}.values()
            ),
        }


class VerificationDocument(db.Model):
    """Justificatif obligatoire (inscription étudiant ou statut enseignant)."""

    __tablename__ = "verification_documents"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    fichier = db.Column(db.String(255), nullable=False)
    statut = db.Column(db.String(30), default="en_attente")
    date_upload = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="verification_documents")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "fichier": self.fichier,
            "statut": self.statut,
            "date_upload": self.date_upload.isoformat() if self.date_upload else None,
        }