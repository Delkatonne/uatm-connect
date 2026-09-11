from datetime import datetime

from app.extensions import db
from app.models.user import gen_uuid

DOCUMENT_TYPES = [
    "cours",
    "exercice",
    "devoir",
    "td",
    "correction",
    "examen",
    "complementaire",
]


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    fichier = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # voir DOCUMENT_TYPES
    teacher_id = db.Column(db.String(36), db.ForeignKey("teachers.id"), nullable=True)
    class_id = db.Column(db.String(36), db.ForeignKey("classes.id"), nullable=False)
    subject_id = db.Column(db.String(36), db.ForeignKey("subjects.id"), nullable=False)
    date_publication = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("Teacher")
    classe = db.relationship("ClassGroup")
    subject = db.relationship("Subject")

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "description": self.description,
            "fichier": self.fichier,
            "type": self.type,
            "matiere": self.subject.nom if self.subject else None,
            "enseignant": self.teacher.user.nom_complet
            if self.teacher and self.teacher.user
            else "Administration",
            "classe_id": self.class_id,
            "date_publication": self.date_publication.isoformat()
            if self.date_publication
            else None,
        }


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    titre = db.Column(db.String(200), nullable=False)
    classe_id = db.Column(db.String(36), db.ForeignKey("classes.id"), nullable=False)
    matiere_id = db.Column(db.String(36), db.ForeignKey("subjects.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure = db.Column(db.String(5), nullable=False)  # "08:00"
    salle = db.Column(db.String(100), nullable=True)
    document_id = db.Column(db.String(36), db.ForeignKey("documents.id"), nullable=True)

    classe = db.relationship("ClassGroup")
    subject = db.relationship("Subject")

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "matiere": self.subject.nom if self.subject else None,
            "date": self.date.isoformat() if self.date else None,
            "heure": self.heure,
            "salle": self.salle,
            "classe_id": self.classe_id,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    lu = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "message": self.message,
            "lu": self.lu,
            "date": self.date.isoformat() if self.date else None,
        }


class AcademicProgram(db.Model):
    """Programme annuel / calendrier / note de service envoyés par l'admin."""

    __tablename__ = "academic_programs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    titre = db.Column(db.String(200), nullable=False)
    fichier = db.Column(db.String(255), nullable=False)
    annee_academique = db.Column(db.String(9), nullable=True)
    destinataire_type = db.Column(db.String(30), nullable=False)  # classe / role / user
    destinataire_id = db.Column(db.String(36), nullable=True)
    date_publication = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "fichier": self.fichier,
            "annee_academique": self.annee_academique,
            "destinataire_type": self.destinataire_type,
            "destinataire_id": self.destinataire_id,
            "date_publication": self.date_publication.isoformat()
            if self.date_publication
            else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    adresse_ip = db.Column(db.String(45), nullable=True)
