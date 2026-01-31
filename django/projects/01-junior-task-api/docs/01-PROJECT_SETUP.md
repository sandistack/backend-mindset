# 🛠️ Step 1: Project Setup

**Waktu:** 2-3 jam  
**Prerequisite:** Python 3.10+, pip, virtualenv

---

## 🎯 Tujuan

- Setup virtual environment
- Install dependencies
- Konfigurasi settings (base, development, production)
- Setup PostgreSQL (opsional, bisa SQLite dulu)

---

## 📋 Tasks

### 1.1 Buat Virtual Environment

```bash
# Buat folder project
mkdir task-api && cd task-api

# Buat virtual environment
python -m venv venv

# Aktivasi
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 1.2 Install Dependencies

Buat `requirements.txt`:

```
django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt>=5.3
django-filter>=23.0
django-cors-headers>=4.0
python-dotenv>=1.0
psycopg2-binary>=2.9  # untuk PostgreSQL
drf-spectacular>=0.26  # API documentation
```

```bash
pip install -r requirements.txt
```

### 1.3 Buat Django Project

```bash
django-admin startproject config .
```

### 1.4 Reorganisasi Settings

**Tujuan:** Pisahkan settings untuk development dan production.

**Referensi:** [ARCHITECTURE.md](../../../docs/01-fundamentals/ARCHITECTURE.md) - Bagian Settings Organization

Buat struktur:
```
config/
├── __init__.py
├── settings/
│   ├── __init__.py
│   ├── base.py        # Shared settings
│   ├── development.py # Dev-specific
│   └── production.py  # Prod-specific
├── urls.py
└── wsgi.py
```

---

## 📝 Yang Harus Dikonfigurasi

### Di `base.py`:

1. **INSTALLED_APPS** - Tambahkan:
   - `rest_framework`
   - `rest_framework_simplejwt`
   - `django_filters`
   - `corsheaders`
   - `drf_spectacular`

2. **REST_FRAMEWORK** - Konfigurasi:
   - Default authentication (JWT)
   - Default permission (IsAuthenticated)
   - Default pagination class
   - Default filter backends

3. **SIMPLE_JWT** - Konfigurasi:
   - Access token lifetime
   - Refresh token lifetime
   - Rotate refresh tokens

4. **AUTH_USER_MODEL** - Akan diset ke custom user model

### Di `development.py`:

1. DEBUG = True
2. ALLOWED_HOSTS = ['localhost', '127.0.0.1']
3. Database SQLite
4. CORS_ALLOW_ALL_ORIGINS = True

### Di `production.py`:

1. DEBUG = False
2. ALLOWED_HOSTS dari environment variable
3. Database PostgreSQL
4. Security settings (HTTPS, HSTS, dll)

---

## 📁 Buat Apps Folder

```bash
mkdir apps
mkdir apps/authentication
mkdir apps/tasks
mkdir apps/core

# Buat apps
cd apps
django-admin startapp authentication
django-admin startapp tasks
django-admin startapp core
cd ..
```

Update `apps.py` di setiap app untuk path yang benar:
```python
# apps/authentication/apps.py
class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'  # Perhatikan prefix 'apps.'
```

---

## ✅ Checklist

- [ ] Virtual environment aktif
- [ ] Semua dependencies terinstall
- [ ] Settings terpisah (base, dev, prod)
- [ ] REST Framework terkonfigurasi
- [ ] JWT settings terkonfigurasi
- [ ] Apps folder structure siap
- [ ] `python manage.py check` tidak ada error

---

## 🔗 Referensi

- [ARCHITECTURE.md](../../../docs/01-fundamentals/ARCHITECTURE.md) - Struktur folder Django
- [RESPONSE_SCHEMA.md](../../../docs/01-fundamentals/RESPONSE_SCHEMA.md) - Standard response format

---

## ➡️ Next Step

Lanjut ke [02-USER_AUTH.md](02-USER_AUTH.md) - Setup Custom User & JWT Authentication
