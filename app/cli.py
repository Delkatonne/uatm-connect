import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User, RoleEnum, AccountStatusEnum, Program, ProgramOption, StudyYear


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
    click.echo("Seed académique terminé.")