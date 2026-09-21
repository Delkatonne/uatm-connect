import os

from flask import Flask

from app.config import config_by_name
from app.extensions import db, migrate, jwt, bcrypt, cors, mail


def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    mail.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.teacher import teacher_bp
    from app.routes.academic import academic_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(academic_bp)
    app.register_blueprint(admin_bp)

    from app.cli import register_cli

    register_cli(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app