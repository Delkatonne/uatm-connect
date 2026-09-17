import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User, RoleEnum, AccountStatusEnum, Program, ProgramOption, StudyYear, Center


@click.command("create-admin")
@click.option("--nom", prompt="Nom complet", help="Nom complet de l'administrateur.")
@click.option("--email", prompt="E-mail", help="E-mail de connexion.")
@click.option(
    "--mot-de-passe",
    prompt="Mot de passe",
    hide_input=True,
    confirmation_prompt=True,
    help="Mot de passe du compte.",
)
@with_appcontext
def create_admin(nom, email, mot_de_passe):
    """Crée un compte administration, actif immédiatement (pas de validation requise)."""
    email = email.strip().lower()

    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f"Un compte existe déjà avec cet e-mail ({existing.role.value}).")
        return

    admin = User(
        nom_complet=nom,
        email=email,
        role=RoleEnum.ADMIN,
        statut=AccountStatusEnum.VALIDE,
    )
    admin.set_password(mot_de_passe)

    db.session.add(admin)
    db.session.commit()

    click.echo(f"Compte administration créé : {email}")


def register_cli(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(seed_academic)
    app.cli.add_command(init_db)
    app.cli.add_command(reset_classes)


@click.command("reset-classes")
@with_appcontext
def reset_classes():
    """
    Supprime toutes les classes existantes (créées avant l'ajout du centre
    obligatoire). Libère d'abord les étudiants qui y étaient rattachés.
    À utiliser une seule fois, puis retirer de la Start Command.
    """
    from app.models import ClassGroup, Student

    students = Student.query.filter(Student.classe_id.isnot(None)).all()
    for s in students:
        s.classe_id = None
    db.session.commit()

    classes = ClassGroup.query.all()
    count = len(classes)
    for c in classes:
        db.session.delete(c)
    db.session.commit()

    click.echo(f"{count} classe(s) supprimée(s). {len(students)} étudiant(s) libéré(s) de leur classe.")


@click.command("init-db")
@with_appcontext
def init_db():
    """Crée les tables directement depuis les modèles (sans passer par Alembic)."""
    db.create_all()
    click.echo("Tables créées (ou déjà à jour).")


@click.command("seed-academic")
@with_appcontext
def seed_academic():
    """Crée les filières, options et années d'étude de base de GASA Formation."""

    study_years_data = [
        ("1ère année", 1),
        ("2e année", 2),
        ("3e année", 3),
        ("Master 1", 4),
        ("Master 2", 5),
    ]
    for nom, niveau in study_years_data:
        if not StudyYear.query.filter_by(nom=nom).first():
            db.session.add(StudyYear(nom=nom, niveau=niveau))
    db.session.commit()

    programs_data = {
        "GE": {
            "nom": "Génie Électrique",
            "options": [
                ("SIL", "Système Informatique et Logiciel"),
                ("SI", "Système Industriel"),
                ("ER", "Énergie Renouvelable"),
                ("FCL", "Froid et Climatisation"),
                ("SECU", "Sécurité Informatique"),
            ],
        },
        "SG": {
            "nom": "Sciences de Gestion",
            "options": [
                ("BFA", "Banque, Finance, Assurance"),
                ("EGP", "Économie, Gestion des Projets"),
                ("FCA", "FCA"),
            ],
        },
        "AGRO": {
            "nom": "Sciences Agronomiques",
            "options": [],
        },
        "RID": {
            "nom": "Relations Internationales / Diplomatie",
            "options": [
                ("RI", "Relations Internationales"),
                ("DIPLO", "Diplomatie"),
            ],
        },
        "SJ": {
            "nom": "Sciences Juridiques",
            "options": [],
        },
    }

    for prog_code, prog_info in programs_data.items():
        program = Program.query.filter_by(code=prog_code).first()
        if not program:
            program = Program(nom=prog_info["nom"], code=prog_code)
            db.session.add(program)
            db.session.flush()
            click.echo(f"Filière créée : {prog_info['nom']} ({prog_code})")

        for opt_code, opt_nom in prog_info["options"]:
            existing = ProgramOption.query.filter_by(
                program_id=program.id, code=opt_code
            ).first()
            if not existing:
                db.session.add(
                    ProgramOption(nom=opt_nom, code=opt_code, program_id=program.id)
                )
                click.echo(f"  Option créée : {opt_nom} ({opt_code})")

    db.session.commit()

    for centre_nom in ["Porto-Novo", "Calavi", "Akpakpa", "Gbégamey"]:
        if not Center.query.filter_by(nom=centre_nom).first():
            db.session.add(Center(nom=centre_nom))
            click.echo(f"Centre créé : {centre_nom}")

    db.session.commit()
    click.echo("Seed académique terminé.")