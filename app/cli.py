import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User, RoleEnum, AccountStatusEnum


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