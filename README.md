# UATM Connect — Backend + pages Login / Espace étudiant

## Démarrage du backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurer la base de données (PostgreSQL) et les secrets
export DATABASE_URL=postgresql://user:password@localhost:5432/uatm_connect
export SECRET_KEY=change-moi
export JWT_SECRET_KEY=change-moi-aussi

flask db init
flask db migrate -m "Structure initiale"
flask db upgrade

python run.py
```

L'API démarre sur `http://localhost:5000/api`.

## Frontend (pages statiques)

Ouvrir `frontend/login.html` dans un navigateur, ou servir le dossier `frontend/`
avec un serveur statique (ex: `python -m http.server` depuis `frontend/`).

Si l'API tourne sur une autre URL, définir avant chargement des scripts :

```html
<script>window.__UATM_API_BASE_URL__ = "https://mon-api.example.com/api";</script>
```

## Ce qui est fonctionnel

- **Modèles** : users, students, teachers, programs, options, study_years,
  classes, subjects, teacher_classes, teacher_subjects, verification_documents,
  documents, exams, notifications, academic_programs, audit_logs
- **Auth** : `POST /api/auth/login`, `POST /api/auth/register/student`
  (multipart avec justificatif obligatoire)
- **Espace étudiant** :
  - `GET /api/student/me`
  - `GET /api/student/documents?type=cours|devoir|exercice|...`
  - `GET /api/student/exams`
  - `GET /api/student/notifications`
  - Toutes protégées par JWT + rôle `etudiant` + compte `valide`
- **Pages** : `login.html` (connexion multi-rôle), `student-dashboard.html`
  (accueil, cours, devoirs, examens, notifications)

## Prochaines étapes suggérées

1. Validation admin (routes pour valider/refuser un compte, affecter une classe)
2. Inscription et espace enseignant (publication de documents)
3. Filtrage dynamique filière → option → année → classe pour le formulaire d'inscription
4. Peupler `study_years` / `programs` / `options` de départ via une commande seed
