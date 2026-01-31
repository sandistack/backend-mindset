# TASK API - DJANGO

## Setup Virtual Environment

```bash
# Buat folder project
mkdir task-api
cd task-api

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Pastikan muncul (venv) di terminal

```

## Dependencies

```bash
pip install Django==4.2.7                         # Versi Django terbaru
pip install djangorestframework==3.14.0           # DRF terbaru
pip install djangorestframework-simplejwt==5.3.0  # Simple JWT terbaru
pip install python-decouple==3.8                  # Untuk mengelola environment variables
pip install psycopg2-binary==2.9.9                # PostgreSQL adapter

# optional
pip install django-cors-headers                # Untuk mengelola CORS
pip install django-filter                      # Untuk filtering di DRF
pip install pytest-django                      # Untuk testing dengan pytest
pip install gunicorn                           # WSGI server untuk deployment
pip install dj-database-url                    # Untuk mengelola database URL di production
pip install whitenoise                         # Untuk melayani static files di production

# Save dependencies
pip freeze > requirements.txt
```

## Create Django Project

```bash
# Bikin project Django (nama: config)
django-admin startproject config .

# Struktur sekarang:
# task-api/
# ├── venv/
# ├── config/
# │   ├── __init__.py
# │   ├── settings.py
# │   ├── urls.py
# │   ├── asgi.py
# │   └── wsgi.py
# ├── manage.py
# └── requirements.txt
```

## Restructure settings.py

```bash
# Masuk ke folder config
cd config

# Buat folder settings
mkdir settings

# Buat files
touch settings/__init__.py
touch settings/base.py
touch settings/development.py
touch settings/production.py

# Balik ke root
cd ..
``` 

```bash
# Linux/Mac:
mv config/settings.py config/settings/base.py

# Windows:
# Manual: rename settings.py jadi base.py, pindah ke folder settings/
```

## Create Apps

```bash
# Buat folder apps
mkdir apps
cd apps

# Create core app (global utilities)
python ../manage.py startapp core

# Create authentication app
python ../manage.py startapp authentication

# Create tasks app
python ../manage.py startapp tasks

# Balik ke root
cd ..
```



**Struktur sekarang:**
```
task-api/
├── venv/
├── apps/
│   ├── core/
│   ├── authentication/
│   └── tasks/
├── config/
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
├── manage.py
└── requirements.txt
```

## Setup Files (.env.example, gitignore)

```bash
cat > .env.example << 'EOF'
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True

# Database
DB_ENGINE=django.db.backends.postgresql
DATABASE_NAME=task_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
EOF

cp .env.example .env
```

```bash
cat > .gitignore << 'EOF'
# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class

# Virtual Environment
venv/
env/
ENV/

# Django
*.log
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environment variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/*.log
EOF
``` 

## Test Run Server

```bash
# Generate secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Copy output, paste ke .env
# SECRET_KEY=<paste-here>

# Run server
python manage.py runserver

# Buka browser: http://127.0.0.1:8000/
# Kalau muncul "The install worked successfully!" berarti SUCCESS!
```

## Make Initial Migration and Create Superuser

```bash
python manage.py makemigrations
# Output:
# Migrations for 'auth':
#   auth/migrations/0001_initial.py
#     - Create model User
#     - Create model Group
#     - Create model Permission
# ...

python manage.py migrate
# Output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   ...

python manage.py createsuperuser
# Ikuti prompt untuk buat superuser
```

