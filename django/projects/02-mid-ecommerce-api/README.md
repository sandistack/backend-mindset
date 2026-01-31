# 🛒 Project 02: E-Commerce API

**Level:** Mid  
**Durasi:** 3-4 Minggu  
**Difficulty:** ⭐⭐⭐☆☆

---

## 🎯 Tujuan Project

Membangun REST API lengkap untuk e-commerce dengan fitur product catalog, shopping cart, order management, payment integration, dan reporting. Project ini mengimplementasikan fitur-fitur production-ready yang umum di dunia kerja.

---

## 📋 Fitur yang Akan Dibuat

### Product Management
- [x] Product CRUD dengan variants (size, color)
- [x] Product categories & subcategories
- [x] Product images (multiple upload)
- [x] Inventory management
- [x] Product search & filtering

### Shopping Cart
- [x] Add/remove items
- [x] Update quantities
- [x] Apply discount codes
- [x] Cart persistence (guest & logged in)

### Order Management
- [x] Checkout process
- [x] Order status tracking
- [x] Order history
- [x] Invoice generation

### Advanced Features
- [x] **File Upload** - Product images ke S3
- [x] **Email** - Order confirmation, shipping updates
- [x] **Export** - Sales reports (PDF/Excel)
- [x] **Payment** - Midtrans/Stripe integration

---

## 🏗️ Tech Stack

```
Django 4.2+
Django REST Framework 3.14+
PostgreSQL
Redis (untuk cart caching)
Celery (untuk async tasks)
AWS S3 (untuk file storage)
Midtrans/Stripe (payment gateway)
```

---

## 📊 Database Schema

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Category  │       │   Product   │       │   Variant   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │<──────│ category_id │       │ id          │
│ name        │       │ id          │<──────│ product_id  │
│ parent_id   │──┐    │ name        │       │ sku         │
│ slug        │  │    │ description │       │ size        │
└─────────────┘  └───>│ base_price  │       │ color       │
                      │ is_active   │       │ price       │
                      └─────────────┘       │ stock       │
                                            └─────────────┘
                            │
                            │
                      ┌─────────────┐       ┌─────────────┐
                      │ ProductImage│       │    Cart     │
                      ├─────────────┤       ├─────────────┤
                      │ id          │       │ id          │
                      │ product_id  │       │ user_id     │
                      │ image_url   │       │ session_key │
                      │ is_primary  │       │ created_at  │
                      │ order       │       └─────────────┘
                      └─────────────┘              │
                                                   │
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Order    │       │  OrderItem  │       │  CartItem   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │<──────│ order_id    │       │ cart_id     │
│ user_id     │       │ variant_id  │       │ variant_id  │
│ order_number│       │ quantity    │       │ quantity    │
│ status      │       │ price       │       └─────────────┘
│ total       │       │ subtotal    │
│ payment_id  │       └─────────────┘
│ shipping_*  │
│ created_at  │
└─────────────┘

┌─────────────┐       ┌─────────────┐
│  Discount   │       │   Payment   │
├─────────────┤       ├─────────────┤
│ id          │       │ id          │
│ code        │       │ order_id    │
│ type        │       │ amount      │
│ value       │       │ method      │
│ min_order   │       │ status      │
│ valid_until │       │ provider_id │
│ usage_limit │       │ paid_at     │
└─────────────┘       └─────────────┘
```

---

## 📁 Struktur Folder

```
ecommerce-api/
├── manage.py
├── requirements.txt
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── authentication/     # From Project 01
    ├── core/
    │   ├── pagination.py
    │   ├── permissions.py
    │   ├── storage.py      # S3 storage backend
    │   └── email.py        # Email service
    ├── products/
    │   ├── models.py       # Category, Product, Variant, Image
    │   ├── serializers.py
    │   ├── views.py
    │   ├── filters.py
    │   ├── services.py     # Business logic
    │   └── tasks.py        # Celery tasks
    ├── cart/
    │   ├── models.py       # Cart, CartItem
    │   ├── serializers.py
    │   ├── views.py
    │   └── services.py     # Cart logic
    ├── orders/
    │   ├── models.py       # Order, OrderItem, Discount
    │   ├── serializers.py
    │   ├── views.py
    │   ├── services.py     # Order processing
    │   └── tasks.py        # Email notifications
    ├── payments/
    │   ├── models.py       # Payment
    │   ├── views.py
    │   ├── services.py     # Payment gateway integration
    │   └── webhooks.py     # Payment callbacks
    └── reports/
        ├── views.py
        ├── services.py     # Report generation
        └── tasks.py        # Background export
```

---

## 📚 Step-by-Step Guide

| Step | File | Deskripsi | Waktu |
|------|------|-----------|-------|
| 1 | [01-PROJECT_SETUP.md](docs/01-PROJECT_SETUP.md) | Multi-app architecture, Redis, Celery | 3-4 jam |
| 2 | [02-PRODUCT_CATALOG.md](docs/02-PRODUCT_CATALOG.md) | Product, Category, Variant models | 6-8 jam |
| 3 | [03-SHOPPING_CART.md](docs/03-SHOPPING_CART.md) | Cart implementation | 4-6 jam |
| 4 | [04-ORDER_MANAGEMENT.md](docs/04-ORDER_MANAGEMENT.md) | Order processing | 6-8 jam |
| 5 | [05-FILE_UPLOAD.md](docs/05-FILE_UPLOAD.md) | Product images, S3 | 4-6 jam |
| 6 | [06-EMAIL_NOTIFICATION.md](docs/06-EMAIL_NOTIFICATION.md) | Order emails | 4-6 jam |
| 7 | [07-EXPORT_REPORTS.md](docs/07-EXPORT_REPORTS.md) | PDF/Excel reports | 4-6 jam |
| 8 | [08-PAYMENT_INTEGRATION.md](docs/08-PAYMENT_INTEGRATION.md) | Payment gateway | 6-8 jam |

---

## 🎯 API Endpoints

```
Products:
GET    /api/products/                    # List products
GET    /api/products/{slug}/             # Product detail
GET    /api/products/{id}/variants/      # Product variants
GET    /api/categories/                  # Category tree

Admin Products:
POST   /api/admin/products/              # Create product
PUT    /api/admin/products/{id}/         # Update product
DELETE /api/admin/products/{id}/         # Delete product
POST   /api/admin/products/{id}/images/  # Upload images

Cart:
GET    /api/cart/                        # Get cart
POST   /api/cart/items/                  # Add item
PUT    /api/cart/items/{id}/             # Update quantity
DELETE /api/cart/items/{id}/             # Remove item
POST   /api/cart/apply-discount/         # Apply discount code
DELETE /api/cart/discount/               # Remove discount

Orders:
POST   /api/orders/                      # Create order (checkout)
GET    /api/orders/                      # Order history
GET    /api/orders/{id}/                 # Order detail
GET    /api/orders/{id}/invoice/         # Download invoice PDF

Payments:
POST   /api/payments/create/             # Initiate payment
POST   /api/payments/webhook/            # Payment callback
GET    /api/payments/{id}/status/        # Check payment status

Reports (Admin):
GET    /api/admin/reports/sales/         # Sales report
GET    /api/admin/reports/products/      # Product report
POST   /api/admin/reports/export/        # Export report (async)
GET    /api/admin/reports/export/{id}/   # Download export
```

---

## ✅ Checklist Penyelesaian

### Week 1
- [ ] Project setup dengan Redis & Celery
- [ ] Product catalog (Category, Product, Variant)
- [ ] Product search & filtering
- [ ] Product images upload

### Week 2
- [ ] Shopping cart implementation
- [ ] Discount codes
- [ ] Order creation & status
- [ ] Order emails (Celery)

### Week 3
- [ ] Payment gateway integration
- [ ] Webhook handling
- [ ] Invoice PDF generation
- [ ] Sales reports

### Week 4
- [ ] Excel export
- [ ] Background export jobs
- [ ] Testing
- [ ] Documentation

---

## 🔗 Referensi Dokumentasi

### File Upload
- [FILE_UPLOAD.md](../../docs/04-advanced/FILE_UPLOAD.md) - S3, image processing

### Email
- [EMAIL.md](../../docs/04-advanced/EMAIL.md) - Transactional emails, Celery

### Export
- [EXPORT.md](../../docs/04-advanced/EXPORT.md) - PDF, Excel, CSV

### Background Jobs
- [BACKGROUND_JOBS.md](../../docs/04-advanced/BACKGROUND_JOBS.md) - Celery setup

### Caching
- [CACHING.md](../../docs/04-advanced/CACHING.md) - Redis for cart

---

## 🚀 Setelah Selesai

1. Deploy dengan Docker
2. Setup CI/CD
3. Tambahkan ke portfolio
4. Lanjut ke **Project 03: Collaboration Platform**
