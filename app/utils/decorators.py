from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*allowed_roles):
    """Autorise l'accès uniquement aux rôles listés (ex: role_required('admin'))."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"message": "Accès non autorisé pour ce rôle."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def account_must_be_valide(fn):
    """Bloque l'accès tant que le compte n'est pas validé par l'administration."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("statut") != "valide":
            return (
                jsonify(
                    {
                        "message": "Votre compte n'est pas encore validé.",
                        "statut": claims.get("statut"),
                    }
                ),
                403,
            )
        return fn(*args, **kwargs)

    return wrapper
