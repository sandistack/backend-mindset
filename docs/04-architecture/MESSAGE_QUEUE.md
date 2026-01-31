# 📨 MESSAGE QUEUE - Messaging Systems (Junior → Senior)

Dokumentasi lengkap tentang Message Queue dari konsep dasar hingga advanced patterns.

---

## 🎯 Apa itu Message Queue?

```
Synchronous Communication (Tanpa Message Queue):
┌──────────┐    request     ┌──────────┐
│ Service A│ ─────────────► │ Service B│
│          │ ◄───────────── │          │
└──────────┘    response    └──────────┘
                 (wait)

❌ Problems:
- A waits for B (blocking)
- If B is down, A fails
- B gets overloaded


Asynchronous Communication (Dengan Message Queue):
┌──────────┐              ┌──────────┐              ┌──────────┐
│ Service A│ ──publish──► │  Queue   │ ──consume──► │ Service B│
│(Producer)│              │ (Broker) │              │(Consumer)│
└──────────┘              └──────────┘              └──────────┘
                               │
                     Messages are stored
                      until consumed

✅ Benefits:
- A doesn't wait (non-blocking)
- If B is down, messages wait in queue
- B processes at its own pace
```

---

## 1️⃣ JUNIOR LEVEL - Basic Concepts

### Core Terminology

```
Producer  : Service yang mengirim message
Consumer  : Service yang menerima message
Queue     : Tempat penyimpanan message
Broker    : Server yang manage queue (RabbitMQ, Kafka)
Message   : Data yang dikirim
Exchange  : Router untuk menentukan queue tujuan
Binding   : Aturan routing dari exchange ke queue
```

### Common Message Brokers

| Broker | Best For | Protocol |
|--------|----------|----------|
| **RabbitMQ** | Traditional messaging, complex routing | AMQP |
| **Apache Kafka** | Event streaming, high throughput | Kafka Protocol |
| **Redis** | Simple pub/sub, caching combo | Redis Protocol |
| **Amazon SQS** | Managed AWS queue | HTTP |
| **Google Pub/Sub** | Managed GCP messaging | HTTP/gRPC |

### Use Cases

```
1. Background Jobs
   User upload → Queue → Process video in background

2. Email/Notification
   User register → Queue → Send welcome email

3. Order Processing
   Create order → Queue → Process payment → Queue → Ship

4. Log Aggregation
   Service A logs → Queue → Central log system
   Service B logs ───┘

5. Microservice Communication
   Service A → Queue → Service B (decoupled)
```

---

## 2️⃣ MID LEVEL - RabbitMQ

### Setup RabbitMQ

```yaml
# docker-compose.yml
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3.12-management
    ports:
      - "5672:5672"   # AMQP
      - "15672:15672" # Management UI
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=secret
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

volumes:
  rabbitmq_data:
```

### Basic Publisher/Consumer (Python)

```python
# Install: pip install pika

# publisher.py
import pika
import json

def publish_message(queue_name: str, message: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            credentials=pika.PlainCredentials('admin', 'secret')
        )
    )
    channel = connection.channel()
    
    # Declare queue (creates if not exists)
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Publish message
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
            content_type='application/json'
        )
    )
    
    print(f"Sent: {message}")
    connection.close()

# Usage
publish_message('emails', {
    'to': 'user@example.com',
    'subject': 'Welcome!',
    'body': 'Thanks for joining!'
})
```

```python
# consumer.py
import pika
import json

def callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received: {message}")
    
    # Process message
    send_email(message['to'], message['subject'], message['body'])
    
    # Acknowledge message (remove from queue)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_messages(queue_name: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            credentials=pika.PlainCredentials('admin', 'secret')
        )
    )
    channel = connection.channel()
    
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Fair dispatch - don't give more than 1 message at a time
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback
    )
    
    print(f"Waiting for messages on {queue_name}...")
    channel.start_consuming()

# Run consumer
consume_messages('emails')
```

### Exchange Types

```
1. Direct Exchange
   Route by exact routing key match

   Publisher → Exchange → routing_key="email" → Email Queue
                       → routing_key="sms" → SMS Queue

2. Fanout Exchange  
   Broadcast to ALL bound queues (ignore routing key)

   Publisher → Exchange → Queue A
                       → Queue B
                       → Queue C

3. Topic Exchange
   Route by pattern matching (* = one word, # = zero or more)

   Publisher → Exchange → "order.created" → Order Queue (order.*)
                       → "order.updated" → Order Queue (order.*)
                       → "user.created" → User Queue (user.*)
                       → "payment.failed" → All Queues (#.failed)

4. Headers Exchange
   Route by message headers (not routing key)
```

```python
# Topic Exchange Example
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare topic exchange
channel.exchange_declare(exchange='events', exchange_type='topic')

# Declare and bind queues
channel.queue_declare(queue='order_service')
channel.queue_bind(exchange='events', queue='order_service', routing_key='order.*')

channel.queue_declare(queue='notification_service')
channel.queue_bind(exchange='events', queue='notification_service', routing_key='*.created')
channel.queue_bind(exchange='events', queue='notification_service', routing_key='*.failed')

# Publish events
channel.basic_publish(
    exchange='events',
    routing_key='order.created',
    body='{"order_id": 123}'
)
# Goes to: order_service, notification_service

channel.basic_publish(
    exchange='events',
    routing_key='payment.failed',
    body='{"payment_id": 456}'
)
# Goes to: notification_service only
```

---

## 3️⃣ MID-SENIOR LEVEL - Apache Kafka

### Kafka Concepts

```
┌─────────────────────────────────────────────────────────────┐
│                      Kafka Cluster                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Topic: orders                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Partition 0: [msg1][msg2][msg3][msg4] ──────────►   │    │
│  │ Partition 1: [msg5][msg6][msg7] ──────────────►     │    │
│  │ Partition 2: [msg8][msg9] ────────────────────►     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Producer: Writes to partition (by key or round-robin)      │
│  Consumer Group: Each partition read by one consumer        │
│  Offset: Position in partition (consumer tracks progress)   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Setup Kafka

```yaml
# docker-compose.yml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper
```

### Kafka Producer/Consumer (Python)

```python
# Install: pip install kafka-python

# producer.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None
)

# Send message
producer.send(
    topic='orders',
    key='order-123',  # Same key = same partition
    value={
        'order_id': 123,
        'user_id': 456,
        'total': 99.99,
        'status': 'created'
    }
)

producer.flush()  # Wait for all messages to be sent
producer.close()
```

```python
# consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=['localhost:9092'],
    group_id='order-processor',  # Consumer group
    auto_offset_reset='earliest',  # Start from beginning if no offset
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    print(f"""
    Topic: {message.topic}
    Partition: {message.partition}
    Offset: {message.offset}
    Key: {message.key}
    Value: {message.value}
    """)
    
    # Process message
    order = message.value
    process_order(order)
    
    # Offset auto-committed by default
```

### Kafka vs RabbitMQ

| Feature | RabbitMQ | Kafka |
|---------|----------|-------|
| Model | Message Queue | Event Log |
| Message deleted after | Consumed | Retention period |
| Replay messages | ❌ No | ✅ Yes |
| Ordering | Per queue | Per partition |
| Throughput | ~50k msg/s | ~1M msg/s |
| Best for | Task queues, RPC | Event streaming, logs |
| Complexity | Lower | Higher |

---

## 4️⃣ SENIOR LEVEL - Redis Pub/Sub & Streams

### Redis Pub/Sub

```python
# Install: pip install redis

# Simple but NO persistence (messages lost if no subscriber)

# publisher.py
import redis
import json

r = redis.Redis(host='localhost', port=6379)

r.publish('notifications', json.dumps({
    'type': 'new_order',
    'order_id': 123
}))
```

```python
# subscriber.py
import redis
import json

r = redis.Redis(host='localhost', port=6379)
pubsub = r.pubsub()
pubsub.subscribe('notifications')

for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        print(f"Received: {data}")
```

### Redis Streams (Persistent)

```python
# Redis Streams - persistent message queue

import redis
import json

r = redis.Redis(host='localhost', port=6379)

# Producer
def publish_event(stream: str, event: dict):
    r.xadd(stream, {'data': json.dumps(event)})

publish_event('orders', {'order_id': 123, 'status': 'created'})

# Consumer (with consumer group for scaling)
def create_consumer_group(stream: str, group: str):
    try:
        r.xgroup_create(stream, group, id='0', mkstream=True)
    except redis.ResponseError:
        pass  # Group already exists

def consume_events(stream: str, group: str, consumer: str):
    create_consumer_group(stream, group)
    
    while True:
        messages = r.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: '>'},  # Only new messages
            count=10,
            block=5000  # Wait 5 seconds
        )
        
        for stream_name, stream_messages in messages:
            for msg_id, msg_data in stream_messages:
                event = json.loads(msg_data[b'data'])
                print(f"Processing: {event}")
                
                # Process event
                process_event(event)
                
                # Acknowledge
                r.xack(stream_name, group, msg_id)

# Run consumer
consume_events('orders', 'order-processors', 'consumer-1')
```

---

## 5️⃣ SENIOR LEVEL - Delivery Guarantees

### Message Delivery Semantics

```
1. At-Most-Once (Fire and Forget)
   ┌──────────┐    send    ┌──────────┐
   │ Producer │ ─────────► │ Consumer │
   └──────────┘            └──────────┘
   
   - No ack, no retry
   - Message may be lost
   - Fast, good for metrics/logs

2. At-Least-Once (Acknowledge + Retry)
   ┌──────────┐    send    ┌──────────┐
   │ Producer │ ─────────► │ Consumer │
   │          │ ◄───────── │   ACK    │
   └──────────┘    ack     └──────────┘
   
   - Retry until ack
   - Message may be duplicated
   - Common, need idempotent consumer

3. Exactly-Once (Transaction)
   ┌──────────┐    send    ┌──────────┐
   │ Producer │ ─────────► │ Consumer │
   │          │ ◄───────── │          │
   └──────────┘  commit    └──────────┘
   
   - Complex, expensive
   - Kafka supports this
   - Most difficult to implement
```

### Implementing Idempotency

```python
# At-Least-Once requires idempotent consumers

import redis

r = redis.Redis()

def process_order(order_id: str, order_data: dict):
    # Check if already processed
    if r.sismember('processed_orders', order_id):
        print(f"Order {order_id} already processed, skipping")
        return
    
    # Process order
    create_order_in_db(order_data)
    charge_payment(order_data['payment'])
    
    # Mark as processed (with TTL for cleanup)
    r.sadd('processed_orders', order_id)
    r.expire('processed_orders', 86400 * 7)  # 7 days

# Alternative: Use database unique constraint
def process_order_db(order_id: str, order_data: dict):
    try:
        # order_id has unique constraint
        db.orders.insert(order_id=order_id, **order_data)
    except UniqueViolationError:
        print(f"Order {order_id} already exists, skipping")
        return
```

---

## 6️⃣ SENIOR LEVEL - Advanced Patterns

### Dead Letter Queue (DLQ)

```
When processing fails repeatedly, move to DLQ for investigation

┌──────────┐        ┌─────────────┐        ┌──────────┐
│ Producer │ ─────► │ Main Queue  │ ─────► │ Consumer │
└──────────┘        └──────┬──────┘        └──────────┘
                          │
                    (after N retries)
                          │
                          ▼
                   ┌─────────────┐
                   │ Dead Letter │
                   │    Queue    │
                   └─────────────┘
```

```python
# RabbitMQ DLQ setup
channel.exchange_declare(exchange='main', exchange_type='direct')
channel.exchange_declare(exchange='dlx', exchange_type='direct')

# Main queue with DLQ settings
channel.queue_declare(
    queue='orders',
    durable=True,
    arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'orders-dlq'
    }
)
channel.queue_bind(exchange='main', queue='orders', routing_key='orders')

# DLQ
channel.queue_declare(queue='orders-dlq', durable=True)
channel.queue_bind(exchange='dlx', queue='orders-dlq', routing_key='orders-dlq')

# Consumer with retry logic
def callback(ch, method, properties, body):
    retry_count = (properties.headers or {}).get('x-retry-count', 0)
    
    try:
        process_message(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        if retry_count < 3:
            # Retry with incremented count
            ch.basic_publish(
                exchange='main',
                routing_key='orders',
                body=body,
                properties=pika.BasicProperties(
                    headers={'x-retry-count': retry_count + 1}
                )
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # Send to DLQ (by rejecting without requeue)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
```

### Priority Queue

```python
# RabbitMQ priority queue
channel.queue_declare(
    queue='tasks',
    durable=True,
    arguments={'x-max-priority': 10}
)

# Publish with priority
channel.basic_publish(
    exchange='',
    routing_key='tasks',
    body='high priority task',
    properties=pika.BasicProperties(priority=9)
)

channel.basic_publish(
    exchange='',
    routing_key='tasks',
    body='low priority task',
    properties=pika.BasicProperties(priority=1)
)
```

### Delayed Messages

```python
# RabbitMQ delayed message (using TTL + DLX trick)

# 1. Create delay exchange/queue
channel.exchange_declare(exchange='delay', exchange_type='direct')
channel.queue_declare(
    queue='delay-queue',
    arguments={
        'x-dead-letter-exchange': 'main',
        'x-dead-letter-routing-key': 'orders'
    }
)
channel.queue_bind(exchange='delay', queue='delay-queue', routing_key='delay')

# 2. Publish with TTL (delay)
def publish_delayed(message: dict, delay_ms: int):
    channel.basic_publish(
        exchange='delay',
        routing_key='delay',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            expiration=str(delay_ms)  # Delay in milliseconds
        )
    )

# Usage: Send message to be processed in 5 minutes
publish_delayed({'action': 'send_reminder', 'user_id': 123}, 300000)
```

---

## 7️⃣ EXPERT LEVEL - Event-Driven Architecture

### Event Types

```python
# 1. Domain Events - Something happened
class OrderCreatedEvent:
    order_id: str
    user_id: str
    items: list
    total: float
    created_at: datetime

# 2. Integration Events - For other services
class OrderCreatedIntegrationEvent:
    event_id: str
    event_type: str = "order.created"
    timestamp: datetime
    data: dict  # Minimal data needed by other services

# 3. Commands - Request to do something
class ProcessPaymentCommand:
    order_id: str
    amount: float
    payment_method: str
```

### Event Schema Evolution

```python
# Use schema registry for versioning (e.g., Confluent Schema Registry)

# Version 1
{
    "type": "record",
    "name": "OrderCreated",
    "version": 1,
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "user_id", "type": "string"},
        {"name": "total", "type": "float"}
    ]
}

# Version 2 - Adding field (backward compatible)
{
    "type": "record",
    "name": "OrderCreated",
    "version": 2,
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "user_id", "type": "string"},
        {"name": "total", "type": "float"},
        {"name": "currency", "type": "string", "default": "USD"}  # New field with default
    ]
}
```

### Outbox Pattern

```
Problem: How to atomically update DB and publish message?

❌ Bad: Two operations, not atomic
    1. Save to DB ✓
    2. Publish message ✗ (fails)
    Result: DB updated, but message lost

✅ Good: Outbox Pattern
    1. Save to DB + Save to outbox table (single transaction)
    2. Separate process reads outbox and publishes
```

```python
# Outbox Pattern Implementation
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import Session
import json

class Outbox(Base):
    __tablename__ = 'outbox'
    
    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    published = Column(Boolean, default=False)

def create_order(db: Session, order_data: dict):
    # Single transaction
    with db.begin():
        # 1. Create order
        order = Order(**order_data)
        db.add(order)
        
        # 2. Add to outbox
        outbox_event = Outbox(
            id=str(uuid.uuid4()),
            event_type='order.created',
            payload=json.dumps({
                'order_id': order.id,
                'user_id': order.user_id,
                'total': order.total
            })
        )
        db.add(outbox_event)
    
    return order

# Outbox publisher (separate process/worker)
def publish_outbox_events(db: Session, publisher):
    while True:
        events = db.query(Outbox).filter(
            Outbox.published == False
        ).limit(100).all()
        
        for event in events:
            try:
                publisher.publish(
                    topic=event.event_type,
                    message=event.payload
                )
                event.published = True
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to publish: {e}")
        
        time.sleep(1)
```

---

## 📊 Quick Reference

### Broker Comparison

| Feature | RabbitMQ | Kafka | Redis Streams |
|---------|----------|-------|---------------|
| Throughput | Medium | Very High | High |
| Latency | Low | Low | Very Low |
| Persistence | Yes | Yes | Yes |
| Replay | No | Yes | Yes |
| Ordering | Per Queue | Per Partition | Per Stream |
| Clustering | Yes | Yes | Yes |
| Use Case | Task Queue | Event Stream | Simple Queue |

### When to Use What

```
RabbitMQ:
- Complex routing (exchange types)
- Task queues with priorities
- RPC patterns
- Traditional messaging

Kafka:
- High throughput (millions/sec)
- Event sourcing
- Log aggregation
- Stream processing
- Replay needed

Redis:
- Simple pub/sub
- Already using Redis for caching
- Low latency required
- Less critical data
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Concepts, use cases |
| **Mid** | RabbitMQ basics, exchange types |
| **Mid-Senior** | Kafka, Redis Streams |
| **Senior** | Delivery guarantees, DLQ, patterns |
| **Expert** | Event-driven, Outbox pattern |

**Best Practices:**
- ✅ Use idempotent consumers
- ✅ Implement Dead Letter Queue
- ✅ Add message tracing (correlation ID)
- ✅ Monitor queue depth
- ✅ Set appropriate TTL
- ✅ Handle poison messages
- ✅ Use schema registry for Kafka
- ✅ Implement retry with backoff

**Common Mistakes:**
- ❌ Not acknowledging messages properly
- ❌ No idempotency (duplicate processing)
- ❌ Ignoring DLQ
- ❌ Too large messages (use reference)
- ❌ Not monitoring queue lag
