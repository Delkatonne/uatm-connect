import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Configuration de base, commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi-en-production")

    # Base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/uatm_connect"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-moi-aussi")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Uploads (justificatifs, documents pédagogiques, photos de profil)
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(basedir, "uploads")
    )
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 Mo par fichier
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Délai cible de validation d'un compte (informatif, utilisé pour les rapports)
    VALIDATION_DELAY_HOURS = 24


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///test.db"
    )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
