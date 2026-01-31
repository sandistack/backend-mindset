# ✨ CLEAN CODE - Best Practices (Junior → Senior)

Dokumentasi lengkap tentang menulis code yang bersih, maintainable, dan scalable.

---

## 🎯 Kenapa Clean Code?

**Dirty Code:**
```python
def x(a, b, c):
    if a > 0:
        if b > 0:
            if c > 0:
                return a * b * c
            else:
                return 0
        else:
            return 0
    else:
        return 0
```

**Clean Code:**
```python
def calculate_volume(length, width, height):
    if not all(dim > 0 for dim in [length, width, height]):
        return 0
    return length * width * height
```

**Benefits:**
- ✅ Readable - Easy to understand
- ✅ Maintainable - Easy to modify
- ✅ Testable - Easy to test
- ✅ Debuggable - Easy to find bugs
- ✅ Scalable - Easy to extend

---

## 1️⃣ JUNIOR LEVEL - Naming Conventions

### Variables

```python
# ❌ Bad: Unclear names
x = 100
temp = "john@email.com"
data = [1, 2, 3]
flag = True

# ✅ Good: Descriptive names
max_connections = 100
user_email = "john@email.com"
task_ids = [1, 2, 3]
is_authenticated = True
```

### Functions

```python
# ❌ Bad: Unclear purpose
def process(x):
    pass

def handle_data(data):
    pass

def do_stuff():
    pass

# ✅ Good: Action + Subject
def calculate_total_price(items):
    pass

def validate_email(email):
    pass

def send_welcome_email(user):
    pass

def get_user_by_id(user_id):
    pass

def create_task(title, description):
    pass

def is_valid_password(password):
    pass
```

### Classes

```python
# ❌ Bad: Unclear or wrong naming
class data:
    pass

class HandleUser:
    pass

class user_service:
    pass

# ✅ Good: Nouns, PascalCase
class User:
    pass

class UserService:
    pass

class TaskRepository:
    pass

class EmailNotification:
    pass
```

### Constants

```python
# ❌ Bad: Magic numbers
if user.role == 1:
    pass

if len(password) < 8:
    pass

# ✅ Good: Named constants
ROLE_ADMIN = 1
ROLE_USER = 2
MIN_PASSWORD_LENGTH = 8

if user.role == ROLE_ADMIN:
    pass

if len(password) < MIN_PASSWORD_LENGTH:
    pass
```

---

## 2️⃣ MID LEVEL - Function Design

### Single Responsibility

```python
# ❌ Bad: Does too many things
def process_user_registration(data):
    # Validate data
    if not data.get('email'):
        raise ValueError("Email required")
    if len(data.get('password', '')) < 8:
        raise ValueError("Password too short")
    
    # Create user
    user = User.objects.create(
        email=data['email'],
        password=hash_password(data['password'])
    )
    
    # Send email
    send_mail(
        subject="Welcome!",
        message="Thanks for registering",
        recipient_list=[user.email]
    )
    
    # Log
    logger.info(f"User {user.id} registered")
    
    return user


# ✅ Good: Single responsibility each
def validate_registration_data(data):
    if not data.get('email'):
        raise ValueError("Email required")
    if len(data.get('password', '')) < 8:
        raise ValueError("Password too short")

def create_user(email, password):
    return User.objects.create(
        email=email,
        password=hash_password(password)
    )

def send_welcome_email(user):
    send_mail(
        subject="Welcome!",
        message="Thanks for registering",
        recipient_list=[user.email]
    )

def register_user(data):
    validate_registration_data(data)
    user = create_user(data['email'], data['password'])
    send_welcome_email(user)
    logger.info(f"User {user.id} registered")
    return user
```

### Keep Functions Small

```python
# ❌ Bad: Too long (50+ lines)
def process_order(order_data):
    # 100 lines of code...
    pass


# ✅ Good: Small, focused functions
def validate_order(order_data):
    pass

def calculate_total(items):
    pass

def apply_discount(total, discount_code):
    pass

def create_order(user, items, total):
    pass

def send_order_confirmation(order):
    pass

def process_order(order_data):
    validate_order(order_data)
    total = calculate_total(order_data['items'])
    total = apply_discount(total, order_data.get('discount'))
    order = create_order(order_data['user'], order_data['items'], total)
    send_order_confirmation(order)
    return order
```

### Avoid Side Effects

```python
# ❌ Bad: Hidden side effect
user_count = 0

def get_users():
    global user_count
    users = User.objects.all()
    user_count = len(users)  # Side effect!
    return users


# ✅ Good: Pure function
def get_users():
    return User.objects.all()

def count_users(users):
    return len(users)
```

### Parameter Limit (Max 3-4)

```python
# ❌ Bad: Too many parameters
def create_user(name, email, password, age, city, country, phone, role):
    pass


# ✅ Good: Use object/dict
def create_user(user_data):
    pass

# Or use data class
@dataclass
class UserData:
    name: str
    email: str
    password: str
    age: int = None
    city: str = None

def create_user(data: UserData):
    pass
```

---

## 3️⃣ MID-SENIOR LEVEL - SOLID Principles

### S - Single Responsibility

**One class = One job**

```python
# ❌ Bad: Class does too much
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def save(self):
        # Save to database
        pass
    
    def send_email(self, subject, message):
        # Send email
        pass
    
    def generate_report(self):
        # Generate PDF report
        pass


# ✅ Good: Separate responsibilities
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user):
        pass
    
    def find_by_id(self, user_id):
        pass

class EmailService:
    def send(self, to, subject, message):
        pass

class ReportGenerator:
    def generate_user_report(self, user):
        pass
```

### O - Open/Closed

**Open for extension, closed for modification**

```python
# ❌ Bad: Need to modify class for each new type
class NotificationService:
    def send(self, notification_type, message, recipient):
        if notification_type == "email":
            # Send email
            pass
        elif notification_type == "sms":
            # Send SMS
            pass
        elif notification_type == "push":
            # Send push notification
            pass
        # Need to modify this class for each new type!


# ✅ Good: Extend without modifying
from abc import ABC, abstractmethod

class Notification(ABC):
    @abstractmethod
    def send(self, message, recipient):
        pass

class EmailNotification(Notification):
    def send(self, message, recipient):
        # Send email
        pass

class SMSNotification(Notification):
    def send(self, message, recipient):
        # Send SMS
        pass

class PushNotification(Notification):
    def send(self, message, recipient):
        # Send push notification
        pass

# Add new notification types without modifying existing code
class SlackNotification(Notification):
    def send(self, message, recipient):
        # Send to Slack
        pass

class NotificationService:
    def __init__(self, notification: Notification):
        self.notification = notification
    
    def notify(self, message, recipient):
        self.notification.send(message, recipient)
```

### L - Liskov Substitution

**Subclasses should be substitutable for their base class**

```python
# ❌ Bad: Violates LSP
class Bird:
    def fly(self):
        print("Flying")

class Penguin(Bird):
    def fly(self):
        raise Exception("Penguins can't fly!")  # Breaks substitution


# ✅ Good: Proper abstraction
class Bird(ABC):
    @abstractmethod
    def move(self):
        pass

class FlyingBird(Bird):
    def move(self):
        print("Flying")

class SwimmingBird(Bird):
    def move(self):
        print("Swimming")

class Eagle(FlyingBird):
    pass

class Penguin(SwimmingBird):
    pass

# Both can be used as Bird
def make_bird_move(bird: Bird):
    bird.move()  # Works for all birds!
```

### I - Interface Segregation

**Many specific interfaces better than one general**

```python
# ❌ Bad: Fat interface
class Worker(ABC):
    @abstractmethod
    def work(self):
        pass
    
    @abstractmethod
    def eat(self):
        pass
    
    @abstractmethod
    def sleep(self):
        pass

class Robot(Worker):
    def work(self):
        print("Working")
    
    def eat(self):
        pass  # Robots don't eat!
    
    def sleep(self):
        pass  # Robots don't sleep!


# ✅ Good: Segregated interfaces
class Workable(ABC):
    @abstractmethod
    def work(self):
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self):
        pass

class Sleepable(ABC):
    @abstractmethod
    def sleep(self):
        pass

class Human(Workable, Eatable, Sleepable):
    def work(self):
        print("Working")
    
    def eat(self):
        print("Eating")
    
    def sleep(self):
        print("Sleeping")

class Robot(Workable):
    def work(self):
        print("Working")
```

### D - Dependency Inversion

**Depend on abstractions, not concretions**

```python
# ❌ Bad: Depends on concrete class
class MySQLDatabase:
    def query(self, sql):
        pass

class UserRepository:
    def __init__(self):
        self.db = MySQLDatabase()  # Tight coupling!
    
    def find_all(self):
        return self.db.query("SELECT * FROM users")


# ✅ Good: Depends on abstraction
class Database(ABC):
    @abstractmethod
    def query(self, sql):
        pass

class MySQLDatabase(Database):
    def query(self, sql):
        pass

class PostgresDatabase(Database):
    def query(self, sql):
        pass

class UserRepository:
    def __init__(self, db: Database):  # Dependency injection!
        self.db = db
    
    def find_all(self):
        return self.db.query("SELECT * FROM users")

# Easy to switch database
mysql_repo = UserRepository(MySQLDatabase())
postgres_repo = UserRepository(PostgresDatabase())
```

---

## 4️⃣ SENIOR LEVEL - Code Organization

### DRY (Don't Repeat Yourself)

```python
# ❌ Bad: Repeated code
def create_user(data):
    if not data.get('email'):
        raise ValueError("Email required")
    if '@' not in data.get('email', ''):
        raise ValueError("Invalid email format")
    # Create user...

def update_user(data):
    if not data.get('email'):
        raise ValueError("Email required")
    if '@' not in data.get('email', ''):
        raise ValueError("Invalid email format")
    # Update user...


# ✅ Good: Extract common code
def validate_email(email):
    if not email:
        raise ValueError("Email required")
    if '@' not in email:
        raise ValueError("Invalid email format")

def create_user(data):
    validate_email(data.get('email'))
    # Create user...

def update_user(data):
    validate_email(data.get('email'))
    # Update user...
```

### KISS (Keep It Simple, Stupid)

```python
# ❌ Bad: Overcomplicated
def is_even(number):
    if number % 2 == 0:
        return True
    else:
        return False


# ✅ Good: Simple
def is_even(number):
    return number % 2 == 0


# ❌ Bad: Overcomplicated
def get_discount(user):
    discount = 0
    if user.is_premium:
        discount = discount + 10
    if user.orders_count > 10:
        discount = discount + 5
    return discount


# ✅ Good: Simple
def get_discount(user):
    discount = 10 if user.is_premium else 0
    discount += 5 if user.orders_count > 10 else 0
    return discount
```

### YAGNI (You Ain't Gonna Need It)

```python
# ❌ Bad: Building for hypothetical future
class User:
    def __init__(self):
        self.name = None
        self.email = None
        self.phone = None
        self.fax = None          # Who uses fax?
        self.pager = None        # Really?
        self.telex = None        # What year is this?
        self.backup_email_1 = None
        self.backup_email_2 = None
        self.backup_email_3 = None


# ✅ Good: Build what you need now
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        # Add more fields when actually needed
```

---

## 5️⃣ SENIOR LEVEL - Error Handling

### Be Specific

```python
# ❌ Bad: Catch all exceptions
try:
    result = do_something()
except Exception:
    print("Something went wrong")


# ✅ Good: Specific exceptions
try:
    result = do_something()
except ValueError as e:
    print(f"Invalid value: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except TimeoutError as e:
    print(f"Operation timed out: {e}")
```

### Custom Exceptions

```python
# Define custom exceptions
class TaskException(Exception):
    """Base exception for task operations"""
    pass

class TaskNotFoundError(TaskException):
    """Task not found in database"""
    pass

class TaskValidationError(TaskException):
    """Task validation failed"""
    pass

class TaskPermissionError(TaskException):
    """User doesn't have permission"""
    pass


# Use custom exceptions
def get_task(task_id, user):
    task = Task.objects.filter(id=task_id).first()
    
    if not task:
        raise TaskNotFoundError(f"Task {task_id} not found")
    
    if task.user_id != user.id:
        raise TaskPermissionError("You don't have access to this task")
    
    return task
```

### Early Return

```python
# ❌ Bad: Nested conditions
def process_order(order):
    if order:
        if order.is_valid:
            if order.has_items:
                if order.user.is_active:
                    # Process order
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False


# ✅ Good: Early return (Guard clauses)
def process_order(order):
    if not order:
        return False
    
    if not order.is_valid:
        return False
    
    if not order.has_items:
        return False
    
    if not order.user.is_active:
        return False
    
    # Process order
    return True
```

---

## 6️⃣ EXPERT LEVEL - Design Patterns

### Factory Pattern

```python
class NotificationFactory:
    """Create notification objects based on type"""
    
    @staticmethod
    def create(notification_type: str):
        if notification_type == "email":
            return EmailNotification()
        elif notification_type == "sms":
            return SMSNotification()
        elif notification_type == "push":
            return PushNotification()
        else:
            raise ValueError(f"Unknown type: {notification_type}")


# Usage
notification = NotificationFactory.create("email")
notification.send("Hello!", "user@example.com")
```

### Strategy Pattern

```python
class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, base_price):
        pass

class RegularPricing(PricingStrategy):
    def calculate(self, base_price):
        return base_price

class PremiumPricing(PricingStrategy):
    def calculate(self, base_price):
        return base_price * 0.9  # 10% discount

class VIPPricing(PricingStrategy):
    def calculate(self, base_price):
        return base_price * 0.8  # 20% discount


class Order:
    def __init__(self, pricing_strategy: PricingStrategy):
        self.pricing_strategy = pricing_strategy
    
    def calculate_total(self, base_price):
        return self.pricing_strategy.calculate(base_price)


# Usage
regular_order = Order(RegularPricing())
print(regular_order.calculate_total(100))  # 100

vip_order = Order(VIPPricing())
print(vip_order.calculate_total(100))  # 80
```

### Repository Pattern

```python
class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id):
        pass
    
    @abstractmethod
    def save(self, user):
        pass
    
    @abstractmethod
    def delete(self, user):
        pass


class SQLUserRepository(UserRepository):
    def find_by_id(self, user_id):
        return User.objects.get(id=user_id)
    
    def save(self, user):
        user.save()
    
    def delete(self, user):
        user.delete()


class InMemoryUserRepository(UserRepository):
    """For testing"""
    def __init__(self):
        self.users = {}
    
    def find_by_id(self, user_id):
        return self.users.get(user_id)
    
    def save(self, user):
        self.users[user.id] = user
    
    def delete(self, user):
        del self.users[user.id]
```

---

## 7️⃣ EXPERT LEVEL - Code Review Checklist

### ✅ Readability
- [ ] Clear variable/function names
- [ ] Comments for complex logic
- [ ] Consistent formatting
- [ ] No magic numbers

### ✅ Maintainability
- [ ] Single responsibility
- [ ] Small functions (< 20 lines)
- [ ] DRY (no duplication)
- [ ] Loose coupling

### ✅ Correctness
- [ ] Edge cases handled
- [ ] Error handling
- [ ] Input validation
- [ ] Null checks

### ✅ Performance
- [ ] No N+1 queries
- [ ] Efficient algorithms
- [ ] Proper indexing
- [ ] Caching where needed

### ✅ Security
- [ ] Input sanitization
- [ ] No hardcoded secrets
- [ ] Proper authentication
- [ ] SQL injection prevention

### ✅ Testing
- [ ] Unit tests exist
- [ ] Edge cases tested
- [ ] Mocking external services
- [ ] Good coverage

---

## 📊 Quick Reference

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variable | snake_case | `user_name`, `is_active` |
| Function | snake_case | `get_user()`, `calculate_total()` |
| Class | PascalCase | `UserService`, `TaskRepository` |
| Constant | UPPER_SNAKE | `MAX_RETRIES`, `API_URL` |
| Private | _prefix | `_internal_method()` |
| Module | snake_case | `user_service.py` |

### Function Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `get_` | Retrieve data | `get_user_by_id()` |
| `set_` | Set value | `set_password()` |
| `is_` | Boolean check | `is_valid()` |
| `has_` | Has something | `has_permission()` |
| `can_` | Ability check | `can_edit()` |
| `create_` | Create new | `create_user()` |
| `update_` | Update existing | `update_profile()` |
| `delete_` | Remove | `delete_task()` |
| `validate_` | Validation | `validate_email()` |
| `calculate_` | Computation | `calculate_total()` |
| `send_` | Send action | `send_email()` |
| `process_` | Complex operation | `process_order()` |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Naming conventions, basic formatting |
| **Mid** | Single responsibility, small functions |
| **Mid-Senior** | SOLID principles |
| **Senior** | DRY, KISS, YAGNI, error handling |
| **Expert** | Design patterns, code review |

**Golden Rules:**
- ✅ Write code for humans, not computers
- ✅ Keep functions small and focused
- ✅ Use meaningful names
- ✅ Don't repeat yourself
- ✅ Handle errors gracefully
- ✅ Test your code
- ✅ Review before commit

**Quote:**
> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler
