# 🏗️ MICROSERVICES - Arsitektur Microservices (Junior → Senior)

Dokumentasi lengkap tentang arsitektur Microservices dari konsep dasar hingga advanced patterns.

---

## 🎯 Monolith vs Microservices

### Monolithic Architecture

```
┌─────────────────────────────────────────┐
│              Monolith App               │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  User   │ │  Order  │ │ Product │   │
│  │ Module  │ │ Module  │ │ Module  │   │
│  └────┬────┘ └────┬────┘ └────┬────┘   │
│       │          │          │          │
│       └──────────┼──────────┘          │
│                  │                      │
│         ┌────────▼────────┐            │
│         │    Database     │            │
│         └─────────────────┘            │
└─────────────────────────────────────────┘

✅ Pros:
- Simple development
- Easy debugging
- Single deployment
- ACID transactions

❌ Cons:
- Scaling is all-or-nothing
- Tech stack lock-in
- Large codebase
- Single point of failure
- Long deployment cycles
```

### Microservices Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ User Service  │ │ Order Service │ │Product Service│
│               │ │               │ │               │
│  ┌─────────┐  │ │  ┌─────────┐  │ │  ┌─────────┐  │
│  │ User DB │  │ │  │Order DB │  │ │  │Prod DB  │  │
│  │(Postgres)│  │ │  │(MongoDB)│  │ │  │(Redis)  │  │
│  └─────────┘  │ │  └─────────┘  │ │  └─────────┘  │
└───────────────┘ └───────────────┘ └───────────────┘

✅ Pros:
- Independent scaling
- Technology flexibility
- Fault isolation
- Faster deployments
- Team autonomy

❌ Cons:
- Complex infrastructure
- Network latency
- Data consistency challenges
- Operational overhead
- Debugging difficulties
```

---

## 1️⃣ JUNIOR LEVEL - Basic Concepts

### When to Use What?

| Scenario | Recommendation |
|----------|----------------|
| Startup/MVP | Monolith |
| Small team (<5 devs) | Monolith |
| Simple domain | Monolith |
| Large team (>10 devs) | Consider Microservices |
| Different scaling needs | Microservices |
| Multiple tech stacks | Microservices |
| High availability required | Microservices |

### Core Principles

```
1. Single Responsibility
   Each service does ONE thing well

2. Independence
   Deploy, scale, fail independently

3. Decentralized Data
   Each service owns its data

4. API Communication
   Services talk via well-defined APIs

5. Automation
   CI/CD is essential
```

### Simple Microservice Example

```python
# user_service/main.py (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="User Service")

# In-memory database (use real DB in production)
users_db = {}

class User(BaseModel):
    id: int
    name: str
    email: str

@app.post("/users/")
def create_user(user: User):
    users_db[user.id] = user
    return user

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.get("/health")
def health():
    return {"status": "healthy"}
```

```python
# order_service/main.py (FastAPI)
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI(title="Order Service")

USER_SERVICE_URL = "http://user-service:8000"

orders_db = {}

@app.post("/orders/")
async def create_order(user_id: int, product: str, quantity: int):
    # Call User Service to verify user exists
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=400, detail="User not found")
    
    order_id = len(orders_db) + 1
    order = {
        "id": order_id,
        "user_id": user_id,
        "product": product,
        "quantity": quantity,
        "status": "pending"
    }
    orders_db[order_id] = order
    return order
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  user-service:
    build: ./user_service
    ports:
      - "8001:8000"
    
  order-service:
    build: ./order_service
    ports:
      - "8002:8000"
    environment:
      - USER_SERVICE_URL=http://user-service:8000
    depends_on:
      - user-service
```

---

## 2️⃣ MID LEVEL - Service Communication

### Synchronous Communication (REST/gRPC)

```
┌──────────────┐    HTTP/REST    ┌──────────────┐
│   Service A  │ ─────────────► │   Service B  │
│              │ ◄───────────── │              │
└──────────────┘    Response     └──────────────┘

Pros: Simple, immediate response
Cons: Tight coupling, cascade failures
```

```python
# REST Client with retry
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class UserClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def get_user(self, user_id: int):
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
```

### Asynchronous Communication (Message Queue)

```
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│   Service A  │ ──publish──► │Message Queue │ ──consume──► │   Service B  │
│  (Producer)  │              │   (Broker)   │              │  (Consumer)  │
└──────────────┘              └──────────────┘              └──────────────┘

Pros: Loose coupling, resilient, scalable
Cons: Eventual consistency, complexity
```

```python
# Publisher
import aio_pika
import json

async def publish_event(event_type: str, data: dict):
    connection = await aio_pika.connect("amqp://guest:guest@rabbitmq/")
    channel = await connection.channel()
    
    exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
    
    message = aio_pika.Message(
        body=json.dumps(data).encode(),
        content_type="application/json"
    )
    
    await exchange.publish(message, routing_key=event_type)
    await connection.close()

# Usage
await publish_event("order.created", {"order_id": 123, "user_id": 456})
```

```python
# Consumer
async def consume_events():
    connection = await aio_pika.connect("amqp://guest:guest@rabbitmq/")
    channel = await connection.channel()
    
    exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("notification_service")
    
    await queue.bind(exchange, routing_key="order.*")
    
    async for message in queue:
        async with message.process():
            data = json.loads(message.body)
            print(f"Received: {data}")
            # Process message
```

### Communication Patterns Comparison

| Pattern | Use Case | Example |
|---------|----------|---------|
| REST | CRUD operations | Get user details |
| gRPC | High performance | Real-time trading |
| Message Queue | Async processing | Order processing |
| Event Streaming | Real-time data | Analytics |

---

## 3️⃣ MID-SENIOR LEVEL - API Gateway

### API Gateway Pattern

```
                    ┌─────────────────────┐
                    │     API Gateway     │
                    │  - Authentication   │
 Client ──────────► │  - Rate limiting    │
                    │  - Load balancing   │
                    │  - Request routing  │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │ User Service │   │Order Service │   │Prod. Service │
    └──────────────┘   └──────────────┘   └──────────────┘
```

### Kong Gateway Example

```yaml
# docker-compose.yml
version: '3.8'

services:
  kong:
    image: kong:3.4
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
    ports:
      - "8000:8000"  # Proxy
      - "8001:8001"  # Admin API
    volumes:
      - ./kong.yml:/kong/kong.yml
```

```yaml
# kong.yml
_format_version: "3.0"

services:
  - name: user-service
    url: http://user-service:8000
    routes:
      - name: user-route
        paths:
          - /api/users
        strip_path: true

  - name: order-service
    url: http://order-service:8000
    routes:
      - name: order-route
        paths:
          - /api/orders
        strip_path: true

plugins:
  - name: rate-limiting
    config:
      minute: 100
      policy: local
  
  - name: jwt
    config:
      secret_is_base64: false
```

### Simple Gateway with FastAPI

```python
# gateway/main.py
from fastapi import FastAPI, Request, HTTPException
import httpx

app = FastAPI(title="API Gateway")

SERVICES = {
    "users": "http://user-service:8000",
    "orders": "http://order-service:8000",
    "products": "http://product-service:8000",
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    url = f"{SERVICES[service]}/{path}"
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body(),
            params=request.query_params
        )
    
    return response.json()
```

---

## 4️⃣ SENIOR LEVEL - Service Discovery

### Service Discovery Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Registry                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ user-service: [192.168.1.10:8000, 192.168.1.11:8000]│   │
│  │ order-service: [192.168.1.20:8000]                   │   │
│  │ product-service: [192.168.1.30:8000]                 │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
   ┌───────────┐         ┌───────────┐         ┌───────────┐
   │  Service  │         │  Service  │         │  Service  │
   │ Register  │         │ Heartbeat │         │  Lookup   │
   └───────────┘         └───────────┘         └───────────┘
```

### Consul Example

```yaml
# docker-compose.yml
version: '3.8'

services:
  consul:
    image: consul:1.15
    ports:
      - "8500:8500"
    command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0

  user-service:
    build: ./user_service
    environment:
      - CONSUL_HOST=consul
    depends_on:
      - consul
```

```python
# user_service/main.py
import consul
import socket
from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()

def get_ip():
    return socket.gethostbyname(socket.gethostname())

def register_service():
    c = consul.Consul(host='consul')
    c.agent.service.register(
        name='user-service',
        service_id=f'user-service-{get_ip()}',
        address=get_ip(),
        port=8000,
        check=consul.Check.http(f'http://{get_ip()}:8000/health', interval='10s')
    )

def deregister_service():
    c = consul.Consul(host='consul')
    c.agent.service.deregister(f'user-service-{get_ip()}')

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_service()
    yield
    deregister_service()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "healthy"}
```

---

## 5️⃣ SENIOR LEVEL - Circuit Breaker

### Circuit Breaker Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Circuit Breaker States                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────┐     failures     ┌──────────┐                │
│   │  CLOSED  │ ───────────────► │   OPEN   │                │
│   │ (Normal) │                  │ (Failed) │                │
│   └────▲─────┘                  └────┬─────┘                │
│        │                             │                       │
│        │ success                     │ timeout               │
│        │                             ▼                       │
│        │                       ┌───────────┐                │
│        └────────────────────── │ HALF-OPEN │                │
│                                │  (Test)   │                │
│                                └───────────┘                │
└─────────────────────────────────────────────────────────────┘
```

```python
# Circuit Breaker with pybreaker
import pybreaker
import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Create circuit breaker
user_service_breaker = pybreaker.CircuitBreaker(
    fail_max=5,           # Open after 5 failures
    reset_timeout=30,     # Try again after 30 seconds
)

class UserServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    @user_service_breaker
    async def get_user(self, user_id: int):
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()

user_client = UserServiceClient("http://user-service:8000")

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = get_order_from_db(order_id)
    
    try:
        order["user"] = await user_client.get_user(order["user_id"])
    except pybreaker.CircuitBreakerError:
        # Fallback when circuit is open
        order["user"] = {"id": order["user_id"], "name": "Unknown"}
    
    return order
```

---

## 6️⃣ SENIOR LEVEL - Saga Pattern

### Distributed Transactions Problem

```
# Monolith: Simple transaction
BEGIN TRANSACTION
    CREATE order
    UPDATE inventory
    CHARGE payment
COMMIT  # All or nothing

# Microservices: No shared transaction!
Order Service:   CREATE order ✓
Inventory Service: UPDATE inventory ✓
Payment Service:  CHARGE payment ✗  # Failed!
                  
# Now what? Order created, inventory updated, but payment failed!
```

### Saga Pattern - Choreography

```
┌─────────────────────────────────────────────────────────────┐
│                   Choreography Saga                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Order       Inventory      Payment      Notification        │
│  Service     Service        Service      Service             │
│     │            │             │             │               │
│     │ create     │             │             │               │
│     │ order      │             │             │               │
│     ├───────────►│             │             │               │
│     │   order    │ reserve     │             │               │
│     │   created  │ inventory   │             │               │
│     │            ├────────────►│             │               │
│     │            │  inventory  │ process     │               │
│     │            │  reserved   │ payment     │               │
│     │            │             ├────────────►│               │
│     │            │             │  payment    │ send          │
│     │            │             │  completed  │ notification  │
│     │            │             │             │               │
│                                                              │
│  Each service listens for events and publishes new events   │
└─────────────────────────────────────────────────────────────┘
```

```python
# Order Service - Choreography
from fastapi import FastAPI
import aio_pika
import json

app = FastAPI()

@app.post("/orders")
async def create_order(user_id: int, items: list):
    # 1. Create order in pending state
    order = create_order_in_db(user_id, items, status="pending")
    
    # 2. Publish event
    await publish_event("order.created", {
        "order_id": order.id,
        "user_id": user_id,
        "items": items,
        "total": order.total
    })
    
    return order

# Event handler (separate process)
async def handle_events():
    # Listen for payment events
    async for event in consume_events("order_service", "payment.*"):
        if event["type"] == "payment.completed":
            await update_order_status(event["order_id"], "completed")
        elif event["type"] == "payment.failed":
            await update_order_status(event["order_id"], "cancelled")
            # Publish compensating event
            await publish_event("order.cancelled", {"order_id": event["order_id"]})
```

### Saga Pattern - Orchestration

```
┌─────────────────────────────────────────────────────────────┐
│                   Orchestration Saga                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌────────────────┐                        │
│                    │   Saga         │                        │
│                    │ Orchestrator   │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐      │
│  │   Order    │     │ Inventory  │     │  Payment   │      │
│  │  Service   │     │  Service   │     │  Service   │      │
│  └────────────┘     └────────────┘     └────────────┘      │
│                                                              │
│  Orchestrator controls the flow and handles compensation    │
└─────────────────────────────────────────────────────────────┘
```

```python
# Saga Orchestrator
class OrderSaga:
    def __init__(self):
        self.steps = [
            SagaStep(
                action=self.create_order,
                compensation=self.cancel_order
            ),
            SagaStep(
                action=self.reserve_inventory,
                compensation=self.release_inventory
            ),
            SagaStep(
                action=self.process_payment,
                compensation=self.refund_payment
            ),
        ]
        self.completed_steps = []
    
    async def execute(self, order_data: dict):
        try:
            for step in self.steps:
                await step.action(order_data)
                self.completed_steps.append(step)
        except Exception as e:
            # Rollback completed steps in reverse order
            for step in reversed(self.completed_steps):
                await step.compensation(order_data)
            raise e
    
    async def create_order(self, data):
        response = await http_client.post(
            f"{ORDER_SERVICE}/orders",
            json=data
        )
        data["order_id"] = response.json()["id"]
    
    async def cancel_order(self, data):
        await http_client.delete(
            f"{ORDER_SERVICE}/orders/{data['order_id']}"
        )
    
    async def reserve_inventory(self, data):
        await http_client.post(
            f"{INVENTORY_SERVICE}/reservations",
            json={"order_id": data["order_id"], "items": data["items"]}
        )
    
    async def release_inventory(self, data):
        await http_client.delete(
            f"{INVENTORY_SERVICE}/reservations/{data['order_id']}"
        )
    
    async def process_payment(self, data):
        await http_client.post(
            f"{PAYMENT_SERVICE}/payments",
            json={"order_id": data["order_id"], "amount": data["total"]}
        )
    
    async def refund_payment(self, data):
        await http_client.post(
            f"{PAYMENT_SERVICE}/refunds",
            json={"order_id": data["order_id"]}
        )
```

---

## 7️⃣ EXPERT LEVEL - Event Sourcing & CQRS

### Event Sourcing

```
Traditional: Store current state
┌─────────────────────────────────────┐
│ Account: { id: 1, balance: 1000 }   │
└─────────────────────────────────────┘

Event Sourcing: Store all events
┌─────────────────────────────────────┐
│ Event 1: AccountCreated(id=1)       │
│ Event 2: MoneyDeposited(500)        │
│ Event 3: MoneyWithdrawn(200)        │
│ Event 4: MoneyDeposited(700)        │
│                                      │
│ Current state = replay all events   │
│ Balance = 0 + 500 - 200 + 700 = 1000│
└─────────────────────────────────────┘
```

```python
# Event Store
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Event:
    aggregate_id: str
    event_type: str
    data: dict
    timestamp: datetime

class EventStore:
    def __init__(self):
        self.events: List[Event] = []
    
    def append(self, event: Event):
        self.events.append(event)
    
    def get_events(self, aggregate_id: str) -> List[Event]:
        return [e for e in self.events if e.aggregate_id == aggregate_id]

# Account Aggregate
class Account:
    def __init__(self, account_id: str):
        self.id = account_id
        self.balance = 0
        self.events = []
    
    def apply(self, event: Event):
        if event.event_type == "MoneyDeposited":
            self.balance += event.data["amount"]
        elif event.event_type == "MoneyWithdrawn":
            self.balance -= event.data["amount"]
    
    def deposit(self, amount: int):
        event = Event(
            aggregate_id=self.id,
            event_type="MoneyDeposited",
            data={"amount": amount},
            timestamp=datetime.now()
        )
        self.apply(event)
        self.events.append(event)
    
    def withdraw(self, amount: int):
        if amount > self.balance:
            raise ValueError("Insufficient balance")
        event = Event(
            aggregate_id=self.id,
            event_type="MoneyWithdrawn",
            data={"amount": amount},
            timestamp=datetime.now()
        )
        self.apply(event)
        self.events.append(event)
    
    @classmethod
    def from_events(cls, account_id: str, events: List[Event]):
        account = cls(account_id)
        for event in events:
            account.apply(event)
        return account
```

### CQRS (Command Query Responsibility Segregation)

```
┌─────────────────────────────────────────────────────────────┐
│                         CQRS                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│              ┌──────────────────────┐                        │
│   Commands   │    Command Handler   │   (Write)              │
│   ─────────► │ - CreateOrder        │   ─────────►           │
│              │ - UpdateOrder        │   Write DB             │
│              └──────────────────────┘   (Postgres)           │
│                                              │               │
│                                              │ Sync          │
│                                              ▼               │
│              ┌──────────────────────┐   Read DB              │
│   Queries    │    Query Handler     │   (Elasticsearch)      │
│   ─────────► │ - GetOrder           │   ◄─────────           │
│              │ - SearchOrders       │   (Read)               │
│              └──────────────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```python
# CQRS Implementation
from abc import ABC, abstractmethod

# Commands
@dataclass
class CreateOrderCommand:
    user_id: int
    items: List[dict]

@dataclass
class UpdateOrderStatusCommand:
    order_id: int
    status: str

# Command Handler
class OrderCommandHandler:
    def __init__(self, write_db, event_publisher):
        self.write_db = write_db
        self.event_publisher = event_publisher
    
    async def handle_create_order(self, command: CreateOrderCommand):
        order = Order(
            user_id=command.user_id,
            items=command.items,
            status="pending"
        )
        await self.write_db.save(order)
        
        # Publish event for read model sync
        await self.event_publisher.publish("order.created", order.to_dict())
        
        return order

# Queries
@dataclass
class GetOrderQuery:
    order_id: int

@dataclass
class SearchOrdersQuery:
    user_id: int
    status: Optional[str]

# Query Handler
class OrderQueryHandler:
    def __init__(self, read_db):
        self.read_db = read_db  # Elasticsearch
    
    async def handle_get_order(self, query: GetOrderQuery):
        return await self.read_db.get("orders", query.order_id)
    
    async def handle_search_orders(self, query: SearchOrdersQuery):
        return await self.read_db.search("orders", {
            "user_id": query.user_id,
            "status": query.status
        })

# Sync Service (updates read model)
class OrderSyncService:
    def __init__(self, read_db):
        self.read_db = read_db
    
    async def handle_order_created(self, event: dict):
        await self.read_db.index("orders", event["id"], event)
    
    async def handle_order_updated(self, event: dict):
        await self.read_db.update("orders", event["id"], event)
```

---

## 📊 Quick Reference

### Architecture Comparison

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| Complexity | Low | High |
| Deployment | Single | Multiple |
| Scaling | All-or-nothing | Per service |
| Tech Stack | Single | Multiple |
| Team Size | Small | Large |
| Development Speed | Fast (initially) | Slow (initially) |
| Maintenance | Harder over time | Easier per service |

### Communication Patterns

| Pattern | Use Case | Latency | Coupling |
|---------|----------|---------|----------|
| REST | CRUD, simple queries | Low | High |
| gRPC | High performance | Very low | High |
| Message Queue | Async processing | Variable | Low |
| Event Streaming | Real-time | Low | Very low |

### When to Split Monolith

```
1. Team size > 10 developers
2. Different components need different scaling
3. Different release cycles needed
4. Clear bounded contexts exist
5. Technology stack limitations
6. Performance bottlenecks in specific areas
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Monolith vs Microservices concepts |
| **Mid** | REST/Async communication |
| **Mid-Senior** | API Gateway, routing |
| **Senior** | Circuit Breaker, Saga, Discovery |
| **Expert** | Event Sourcing, CQRS |

**Golden Rules:**
- ✅ Start with monolith, extract later
- ✅ Define clear service boundaries
- ✅ Each service owns its data
- ✅ Use async communication when possible
- ✅ Implement circuit breakers
- ✅ Plan for failure
- ✅ Automate everything (CI/CD)
- ✅ Monitor extensively

**Migration Path:**
```
1. Identify bounded contexts
2. Extract one service at a time
3. Start with least critical service
4. Use Strangler Fig pattern
5. Keep shared database temporarily
6. Split database last
```
