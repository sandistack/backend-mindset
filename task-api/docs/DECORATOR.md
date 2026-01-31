# LOGGING STRATEGIES

## 1. File Logging vs Database Logging
- When to use what
- Pros & Cons

## 2. File Logging Setup
- RotatingFileHandler
- TimedRotatingFileHandler
- Auto-cleanup strategies

## 3. Database Audit Logging
- AuditLog model
- log_activity() helper
- Admin dashboard

## 4. Production Best Practices
- Hybrid approach (File + DB)
- Sentry integration
- Email alerts

## 5. Advanced: Decorator Pattern (Senior Level)
- @log_service_call decorator
- DRY principle
- When to upgrade from manual