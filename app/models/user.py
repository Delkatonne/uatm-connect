import enum
import uuid
from datetime import datetime

from app.extensions import db, bcrypt


class RoleEnum(str, enum.Enum):
    ETUDIANT = "etudiant"
    ENSEIGNANT = "enseignant"
    ADMIN = "admin"


class AccountStatusEnum(str, enum.Enum):
    EN_ATTENTE = "en_attente_de_validation"
    VALIDE = "valide"
    REFUSE = "refuse"
    PIECE_A_FOURNIR = "piece_a_fournir"


def gen_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    nom_complet = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    telephone = db.Column(db.String(30), nullable=True)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    statut = db.Column(
        db.Enum(AccountStatusEnum),
        nullable=False,
        default=AccountStatusEnum.EN_ATTENTE,
    )
    photo_profil = db.Column(db.String(255), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_validation = db.Column(db.DateTime, nullable=True)
    valide_par = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    student_profile = db.relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile = db.relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    verification_documents = db.relationship(
        "VerificationDocument", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, mot_de_passe):
        self.mot_de_passe_hash = bcrypt.generate_password_hash(mot_de_passe).decode(
            "utf-8"
        )

    def check_password(self, mot_de_passe):
        return bcrypt.check_password_hash(self.mot_de_passe_hash, mot_de_passe)

    def to_dict(self, include_profile=False):
        data = {
            "id": self.id,
            "nom_complet": self.nom_complet,
            "email": self.email,
            "telephone": self.telephone,
            "role": self.role.value if self.role else None,
            "statut": self.statut.value if self.statut else None,
            "photo_profil": self.photo_profil,
            "date_creation": self.date_creation.isoformat()
            if self.date_creation
            else None,
        }
        if include_profile:
            if self.student_profile:
                data["profil_etudiant"] = self.student_profile.to_dict()
            if self.teacher_profile:
                data["profil_enseignant"] = self.teacher_profile.to_dict()
        return data
