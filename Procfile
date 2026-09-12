web: sh -c "flask db upgrade && flask seed-academic && flask create-admin --nom \"$ADMIN_NAME\" --email \"$ADMIN_EMAIL\" --mot-de-passe \"$ADMIN_PASSWORD\" ; gunicorn run:app"
