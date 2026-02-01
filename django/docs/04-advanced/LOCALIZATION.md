# 🌍 LOCALIZATION - Django (Junior → Senior)

Dokumentasi lengkap tentang internationalization (i18n) dan localization (l10n) di Django.

---

## 🎯 Kenapa Localization Penting?

| Without Localization | With Localization |
|---------------------|-------------------|
| English only | Support multiple languages |
| Fixed date format | Date format per region |
| Fixed currency | Currency per country |
| Limited market | Global market |

**Use Cases:**
- 🌐 **Global SaaS** - Multi-language interface
- 💰 **E-commerce** - Currency per country
- 📅 **Enterprise** - Date format per region
- 🏢 **Multi-national** - Indonesia, English, etc.

---

## 📋 i18n vs l10n

| Term | Meaning | Example |
|------|---------|---------|
| **i18n** (Internationalization) | Prepare code for translation | Extract strings |
| **l10n** (Localization) | Actual translation | Translate to ID, EN |

---

## 1️⃣ JUNIOR LEVEL - Basic Setup

### Enable i18n

```python
# config/settings/base.py
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jakarta'

# Available languages
LANGUAGES = [
    ('en', 'English'),
    ('id', 'Bahasa Indonesia'),
]

# Where to store translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Middleware for language detection
MIDDLEWARE = [
    # ...
    'django.middleware.locale.LocaleMiddleware',
    # ...
]
```

### Mark Strings for Translation

```python
# In views
from django.utils.translation import gettext as _

def my_view(request):
    message = _("Welcome to our application")
    return Response({"message": message})


# In models
from django.utils.translation import gettext_lazy as _

class Task(models.Model):
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ('todo', _("To Do")),
            ('in_progress', _("In Progress")),
            ('done', _("Done")),
        ]
    )
    
    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")


# In serializers
from django.utils.translation import gettext_lazy as _

class TaskSerializer(serializers.Serializer):
    title = serializers.CharField(
        label=_("Title"),
        help_text=_("Enter task title"),
        error_messages={
            'required': _("Title is required"),
            'blank': _("Title cannot be blank"),
        }
    )
```

### Create Translation Files

```bash
# Create locale directory
mkdir -p locale/id/LC_MESSAGES
mkdir -p locale/en/LC_MESSAGES

# Extract strings to .po file
python manage.py makemessages -l id
python manage.py makemessages -l en

# This creates:
# locale/id/LC_MESSAGES/django.po
# locale/en/LC_MESSAGES/django.po
```

### Translate Strings

```po
# locale/id/LC_MESSAGES/django.po
msgid "Welcome to our application"
msgstr "Selamat datang di aplikasi kami"

msgid "Title"
msgstr "Judul"

msgid "Description"
msgstr "Deskripsi"

msgid "Task"
msgstr "Tugas"

msgid "Tasks"
msgstr "Tugas-tugas"

msgid "To Do"
msgstr "Akan Dikerjakan"

msgid "In Progress"
msgstr "Sedang Dikerjakan"

msgid "Done"
msgstr "Selesai"

msgid "Title is required"
msgstr "Judul wajib diisi"
```

### Compile Translations

```bash
# Compile .po to .mo (binary)
python manage.py compilemessages
```

---

## 2️⃣ MID LEVEL - API Localization

### Language Detection

```python
# apps/core/middleware.py
from django.utils import translation
from django.conf import settings

class LanguageMiddleware:
    """
    Detect language from:
    1. Accept-Language header
    2. Query param (?lang=id)
    3. User preference
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        language = None
        
        # 1. From query param
        language = request.GET.get('lang')
        
        # 2. From header
        if not language:
            language = request.headers.get('Accept-Language', '').split(',')[0][:2]
        
        # 3. From user preference
        if not language and request.user.is_authenticated:
            language = getattr(request.user, 'language', None)
        
        # 4. Default
        if not language or language not in dict(settings.LANGUAGES):
            language = settings.LANGUAGE_CODE[:2]
        
        # Activate language
        translation.activate(language)
        request.LANGUAGE_CODE = language
        
        response = self.get_response(request)
        
        # Add Content-Language header
        response['Content-Language'] = language
        
        return response
```

### Localized API Response

```python
# apps/core/response.py
from rest_framework.response import Response
from django.utils.translation import gettext as _

class LocalizedResponse(Response):
    """
    Response with localized messages
    """
    
    def __init__(self, data=None, message=None, **kwargs):
        if message:
            data = data or {}
            data['message'] = _(message) if isinstance(message, str) else message
        
        super().__init__(data, **kwargs)


# Usage
class TaskCreateView(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return LocalizedResponse(
            data={'task': serializer.data},
            message="Task created successfully",
            status=201
        )
```

### Localized Validation Errors

```python
# apps/core/exceptions.py
from rest_framework.views import exception_handler
from django.utils.translation import gettext as _

def localized_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        # Translate common error messages
        if 'detail' in response.data:
            response.data['detail'] = _(str(response.data['detail']))
        
        # Translate field errors
        if isinstance(response.data, dict):
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    response.data[field] = [_(str(error)) for error in errors]
    
    return response


# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.localized_exception_handler',
}
```

### User Language Preference

```python
# apps/authentication/models.py
class User(AbstractUser):
    language = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default='en'
    )


# apps/authentication/views.py
class UpdateLanguageView(APIView):
    def post(self, request):
        language = request.data.get('language', 'en')
        
        if language in dict(settings.LANGUAGES):
            request.user.language = language
            request.user.save()
            
            return Response({
                'success': True,
                'message': _("Language updated successfully")
            })
        
        return Response({
            'success': False,
            'message': _("Invalid language")
        }, status=400)
```

---

## 3️⃣ MID-SENIOR LEVEL - Database Content Translation

### Model Translation dengan django-modeltranslation

```bash
pip install django-modeltranslation
```

```python
# settings.py
INSTALLED_APPS = [
    'modeltranslation',  # Before django.contrib.admin
    'django.contrib.admin',
    # ...
]

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LANGUAGES = ('en', 'id')
```

```python
# apps/products/translation.py
from modeltranslation.translator import translator, TranslationOptions
from .models import Product, Category

class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(Product, ProductTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
```

```python
# apps/products/models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

# After migration, akan ada:
# name, name_en, name_id
# description, description_en, description_id
```

```python
# Usage
product = Product.objects.get(id=1)

# Get translated field (uses current language)
print(product.name)  # Returns name_en or name_id based on active language

# Get specific language
print(product.name_en)  # English name
print(product.name_id)  # Indonesian name

# Set translation
product.name_en = "Running Shoes"
product.name_id = "Sepatu Lari"
product.save()
```

### Manual Translation dengan JSONField

```python
# apps/products/models.py
class Product(models.Model):
    name_translations = models.JSONField(default=dict)
    description_translations = models.JSONField(default=dict)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_name(self, language=None):
        from django.utils.translation import get_language
        lang = language or get_language()
        return self.name_translations.get(lang, self.name_translations.get('en', ''))
    
    def set_name(self, language, value):
        self.name_translations[language] = value


# Usage
product = Product()
product.set_name('en', 'Running Shoes')
product.set_name('id', 'Sepatu Lari')
product.save()

# In view
print(product.get_name())  # Based on current language
print(product.get_name('id'))  # Specific language
```

### Translation Serializer

```python
# apps/products/serializers.py
from rest_framework import serializers

class TranslatedFieldMixin:
    """
    Mixin untuk handle translated fields
    """
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if request:
            language = getattr(request, 'LANGUAGE_CODE', 'en')
            
            # Replace translation fields with localized value
            for field in getattr(self.Meta, 'translated_fields', []):
                translations = getattr(instance, f'{field}_translations', {})
                data[field] = translations.get(language, translations.get('en', ''))
        
        return data


class ProductSerializer(TranslatedFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price']
        translated_fields = ['name', 'description']


# For admin input (all languages)
class ProductAdminSerializer(serializers.ModelSerializer):
    name_en = serializers.CharField(write_only=True)
    name_id = serializers.CharField(write_only=True)
    description_en = serializers.CharField(write_only=True)
    description_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name_en', 'name_id', 'description_en', 'description_id', 'price']
    
    def create(self, validated_data):
        name_translations = {
            'en': validated_data.pop('name_en', ''),
            'id': validated_data.pop('name_id', ''),
        }
        description_translations = {
            'en': validated_data.pop('description_en', ''),
            'id': validated_data.pop('description_id', ''),
        }
        
        product = Product.objects.create(
            name_translations=name_translations,
            description_translations=description_translations,
            **validated_data
        )
        return product
```

---

## 4️⃣ SENIOR LEVEL - Complete Localization System

### Number & Currency Formatting

```python
# apps/core/formatting.py
from django.utils import formats
from django.utils.translation import get_language
from decimal import Decimal
import babel.numbers

def format_currency(amount, currency='IDR'):
    """
    Format currency based on locale
    """
    language = get_language()
    locale_map = {
        'id': 'id_ID',
        'en': 'en_US',
    }
    locale = locale_map.get(language, 'en_US')
    
    return babel.numbers.format_currency(amount, currency, locale=locale)


def format_number(number):
    """
    Format number based on locale
    """
    return formats.number_format(number)


def format_date(date, format_type='SHORT_DATE_FORMAT'):
    """
    Format date based on locale
    """
    return formats.date_format(date, format_type)


# Usage
format_currency(1500000, 'IDR')
# id: Rp 1.500.000
# en: IDR 1,500,000

format_date(date.today())
# id: 01/12/2024
# en: 12/01/2024
```

### Pluralization

```python
# In Python code
from django.utils.translation import ngettext

def get_task_message(count):
    return ngettext(
        "You have %(count)d task",
        "You have %(count)d tasks",
        count
    ) % {'count': count}


# In translation file (django.po)
msgid "You have %(count)d task"
msgid_plural "You have %(count)d tasks"
msgstr[0] "Anda memiliki %(count)d tugas"
msgstr[1] "Anda memiliki %(count)d tugas"
```

### Translation Service

```python
# apps/core/translation_service.py
from django.conf import settings
from django.utils.translation import gettext as _, activate
import json

class TranslationService:
    """
    Service untuk handle translations
    """
    
    @staticmethod
    def get_all_translations(language='en'):
        """
        Get all translations for a language
        Useful for frontend i18n
        """
        from django.utils.translation import trans_real
        
        catalog = trans_real.catalog()
        return dict(catalog._catalog) if catalog else {}
    
    @staticmethod
    def translate_dict(data, language):
        """
        Translate all string values in a dict
        """
        activate(language)
        
        def translate_value(value):
            if isinstance(value, str):
                return _(value)
            elif isinstance(value, dict):
                return {k: translate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [translate_value(item) for item in value]
            return value
        
        return translate_value(data)
    
    @staticmethod
    def get_translations_json(language):
        """
        Get translations as JSON for frontend
        """
        translations = {}
        
        # Common messages
        common_keys = [
            'Save', 'Cancel', 'Delete', 'Edit', 'Create',
            'Success', 'Error', 'Loading', 'No data',
        ]
        
        activate(language)
        for key in common_keys:
            translations[key] = _(key)
        
        return translations


# API endpoint for frontend
class TranslationsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        language = request.GET.get('lang', 'en')
        translations = TranslationService.get_translations_json(language)
        
        return Response({
            'language': language,
            'translations': translations
        })
```

### Timezone Handling

```python
# apps/core/timezone_middleware.py
from django.utils import timezone
import pytz

class TimezoneMiddleware:
    """
    Set timezone based on user preference
    """
    
    TIMEZONE_MAP = {
        'id': 'Asia/Jakarta',
        'en': 'UTC',
        'sg': 'Asia/Singapore',
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # From user preference
        if request.user.is_authenticated:
            tzname = getattr(request.user, 'timezone', None)
        else:
            # From language
            language = getattr(request, 'LANGUAGE_CODE', 'en')
            tzname = self.TIMEZONE_MAP.get(language, 'UTC')
        
        if tzname:
            try:
                timezone.activate(pytz.timezone(tzname))
            except pytz.UnknownTimeZoneError:
                timezone.deactivate()
        else:
            timezone.deactivate()
        
        return self.get_response(request)
```

### Complete i18n Serializer

```python
# apps/core/serializers.py
from rest_framework import serializers
from django.utils import formats, timezone
from django.utils.translation import get_language

class LocalizedSerializer(serializers.Serializer):
    """
    Base serializer with localization support
    """
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return self._localize_data(data)
    
    def _localize_data(self, data):
        if isinstance(data, dict):
            return {k: self._localize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._localize_data(item) for item in data]
        elif isinstance(data, (int, float)) and not isinstance(data, bool):
            return formats.number_format(data)
        elif hasattr(data, 'strftime'):  # datetime
            return formats.date_format(data, 'DATETIME_FORMAT')
        return data


class MoneyField(serializers.DecimalField):
    """
    Custom field for money with localized formatting
    """
    
    def __init__(self, currency='IDR', **kwargs):
        self.currency = currency
        super().__init__(**kwargs)
    
    def to_representation(self, value):
        from apps.core.formatting import format_currency
        return format_currency(value, self.currency)
```

---

## ✅ Checklist Implementasi

| Level | Fitur | Status |
|-------|-------|--------|
| Junior | Enable i18n settings | ⬜ |
| Junior | Mark strings with gettext | ⬜ |
| Junior | Create .po files | ⬜ |
| Mid | Language middleware | ⬜ |
| Mid | Localized API responses | ⬜ |
| Mid | User language preference | ⬜ |
| Senior | Database content translation | ⬜ |
| Senior | Currency/number formatting | ⬜ |
| Senior | Timezone handling | ⬜ |

---

## 🔗 Referensi

- [Django i18n](https://docs.djangoproject.com/en/4.2/topics/i18n/)
- [django-modeltranslation](https://django-modeltranslation.readthedocs.io/)
- [Babel](https://babel.pocoo.org/)
