# 🐳 DOCKER - Containerization (Junior → Senior)

Dokumentasi lengkap tentang Docker dari basic container hingga production deployment.

---

## 🎯 Kenapa Docker?

**Tanpa Docker:**
```
Developer: "It works on my machine!"
DevOps:    "But it doesn't work on server..."
Problem:   Different OS, dependencies, versions
```

**Dengan Docker:**
```
Developer: "Here's my container"
DevOps:    "Works perfectly!"
Solution:  Same environment everywhere
```

**Benefits:**
- ✅ Consistent environment (dev = staging = production)
- ✅ Isolation (no dependency conflicts)
- ✅ Portable (runs anywhere Docker runs)
- ✅ Lightweight (shares host OS kernel)
- ✅ Scalable (easy to replicate)

---

## 1️⃣ JUNIOR LEVEL - Docker Basics

### Install Docker

```bash
# Linux (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Mac/Windows
# Download Docker Desktop from docker.com
```

### Basic Concepts

```
┌─────────────────────────────────────────┐
│              Docker Host                │
│  ┌───────────┐  ┌───────────┐          │
│  │ Container │  │ Container │          │
│  │   App 1   │  │   App 2   │          │
│  └───────────┘  └───────────┘          │
│         ↑              ↑                │
│         └──────────────┘                │
│              Images                     │
└─────────────────────────────────────────┘
```

- **Image:** Blueprint/template (read-only)
- **Container:** Running instance of image
- **Registry:** Store for images (Docker Hub)

### Basic Commands

```bash
# Pull image
docker pull python:3.11
docker pull postgres:15

# List images
docker images

# Run container
docker run python:3.11 python --version

# Run with options
docker run -d \                  # Detached (background)
    --name my-postgres \         # Container name
    -p 5432:5432 \              # Port mapping host:container
    -e POSTGRES_PASSWORD=secret \ # Environment variable
    postgres:15

# List containers
docker ps           # Running only
docker ps -a        # All (including stopped)

# Stop/Start/Restart
docker stop my-postgres
docker start my-postgres
docker restart my-postgres

# Remove container
docker rm my-postgres
docker rm -f my-postgres  # Force (if running)

# Remove image
docker rmi python:3.11

# View logs
docker logs my-postgres
docker logs -f my-postgres  # Follow (tail)

# Execute command in container
docker exec -it my-postgres bash
docker exec my-postgres psql -U postgres
```

---

## 2️⃣ MID LEVEL - Dockerfile

### Basic Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Build & Run

```bash
# Build image
docker build -t my-app:1.0 .
docker build -t my-app:latest .

# Run container
docker run -d -p 8000:8000 my-app:1.0

# Build with different Dockerfile
docker build -f Dockerfile.prod -t my-app:prod .
```

### Dockerfile Best Practices

```dockerfile
# ✅ Good: Use specific version
FROM python:3.11-slim

# ✅ Good: Multi-stage for smaller image
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ✅ Good: Combine RUN commands
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ✅ Good: Use .dockerignore
# .dockerignore
__pycache__
*.pyc
.git
.env
venv/
node_modules/

# ✅ Good: Non-root user
RUN useradd -m appuser
USER appuser
```

### Dockerfile Instructions

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `FROM` | Base image | `FROM python:3.11` |
| `WORKDIR` | Set working directory | `WORKDIR /app` |
| `COPY` | Copy files | `COPY . .` |
| `RUN` | Execute command | `RUN pip install -r requirements.txt` |
| `ENV` | Set environment variable | `ENV DEBUG=false` |
| `EXPOSE` | Document port | `EXPOSE 8000` |
| `CMD` | Default command | `CMD ["python", "app.py"]` |
| `ENTRYPOINT` | Main executable | `ENTRYPOINT ["python"]` |
| `ARG` | Build-time variable | `ARG VERSION=1.0` |
| `VOLUME` | Create mount point | `VOLUME /data` |
| `USER` | Set user | `USER appuser` |

---

## 3️⃣ MID-SENIOR LEVEL - Docker Compose

### Basic docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - DATABASE_URL=postgres://postgres:secret@db:5432/mydb
    depends_on:
      - db
      - redis
    volumes:
      - .:/app  # Mount code for development

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Docker Compose Commands

```bash
# Start all services
docker-compose up
docker-compose up -d  # Detached

# Stop all services
docker-compose down
docker-compose down -v  # Remove volumes too

# Build/rebuild images
docker-compose build
docker-compose up --build

# View logs
docker-compose logs
docker-compose logs -f web  # Follow specific service

# Execute command in service
docker-compose exec web python manage.py migrate
docker-compose exec web bash

# Scale service
docker-compose up --scale web=3

# List containers
docker-compose ps
```

### Development vs Production

```yaml
# docker-compose.yml (base)
version: '3.8'

services:
  web:
    build: .
    environment:
      - DATABASE_URL=postgres://postgres:secret@db:5432/mydb
    depends_on:
      - db


# docker-compose.override.yml (development - auto loaded)
version: '3.8'

services:
  web:
    volumes:
      - .:/app  # Hot reload
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
    command: python manage.py runserver 0.0.0.0:8000


# docker-compose.prod.yml (production)
version: '3.8'

services:
  web:
    image: myapp:${VERSION:-latest}
    environment:
      - DEBUG=false
    command: gunicorn config.wsgi -b 0.0.0.0:8000 --workers 4

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web
```

```bash
# Development (uses docker-compose.yml + docker-compose.override.yml)
docker-compose up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 4️⃣ SENIOR LEVEL - Multi-Stage Builds

### Python Multi-Stage

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY . .

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "config.wsgi", "-b", "0.0.0.0:8000"]
```

### Node.js Multi-Stage

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


# Stage 2: Production
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --production

COPY --from=builder /app/dist ./dist

USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Go Multi-Stage

```dockerfile
# Stage 1: Build
FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .


# Stage 2: Production (minimal image)
FROM alpine:3.18

WORKDIR /app

# Copy only binary
COPY --from=builder /app/main .

RUN adduser -D appuser
USER appuser

EXPOSE 8080
CMD ["./main"]
```

---

## 5️⃣ SENIOR LEVEL - Networking

### Network Types

```bash
# Bridge (default) - containers on same host
docker network create my-network
docker run --network my-network --name app1 myapp
docker run --network my-network --name app2 myapp
# app1 can reach app2 by name

# Host - share host network
docker run --network host myapp

# None - no network
docker run --network none myapp
```

### Docker Compose Networking

```yaml
version: '3.8'

services:
  web:
    build: .
    networks:
      - frontend
      - backend

  db:
    image: postgres:15
    networks:
      - backend

  nginx:
    image: nginx
    networks:
      - frontend

networks:
  frontend:
  backend:
```

---

## 6️⃣ SENIOR LEVEL - Volumes & Data

### Volume Types

```bash
# Named volume (managed by Docker)
docker volume create my-data
docker run -v my-data:/app/data myapp

# Bind mount (host path)
docker run -v /host/path:/container/path myapp
docker run -v $(pwd):/app myapp  # Current directory

# tmpfs (memory only)
docker run --tmpfs /tmp myapp
```

### Docker Compose Volumes

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      # Named volume (persistent)
      - postgres_data:/var/lib/postgresql/data
      # Bind mount (for init scripts)
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  web:
    build: .
    volumes:
      # Development: mount source code
      - .:/app
      # Exclude node_modules
      - /app/node_modules

volumes:
  postgres_data:
```

---

## 7️⃣ EXPERT LEVEL - Production Best Practices

### Security

```dockerfile
# ✅ Use specific versions
FROM python:3.11.6-slim

# ✅ Non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser

# ✅ Read-only filesystem
# docker run --read-only myapp

# ✅ No capabilities
# docker run --cap-drop ALL myapp

# ✅ Scan for vulnerabilities
# docker scout cve myapp:latest
```

### Health Checks

```dockerfile
# In Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
```

```yaml
# In docker-compose.yml
services:
  web:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

### Resource Limits

```yaml
services:
  web:
    build: .
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Logging

```yaml
services:
  web:
    build: .
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 8️⃣ EXPERT LEVEL - CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docker.yml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            myuser/myapp:latest
            myuser/myapp:${{ github.sha }}
```

### Docker Registry

```bash
# Push to Docker Hub
docker login
docker tag myapp:latest username/myapp:latest
docker push username/myapp:latest

# Push to private registry
docker tag myapp:latest registry.example.com/myapp:latest
docker push registry.example.com/myapp:latest

# Push to AWS ECR
aws ecr get-login-password | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag myapp:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
```

---

## 📊 Quick Reference

### Common Commands

| Command | Description |
|---------|-------------|
| `docker build -t name .` | Build image |
| `docker run -d -p 8000:8000 name` | Run container |
| `docker ps` | List running containers |
| `docker logs container` | View logs |
| `docker exec -it container bash` | Enter container |
| `docker-compose up -d` | Start services |
| `docker-compose down` | Stop services |
| `docker system prune` | Clean up |

### Image Size Comparison

| Base Image | Size | Use Case |
|-----------|------|----------|
| `ubuntu:22.04` | ~77MB | General purpose |
| `python:3.11` | ~1GB | Development |
| `python:3.11-slim` | ~120MB | Production |
| `python:3.11-alpine` | ~50MB | Minimal (may have issues) |
| `node:20` | ~1GB | Development |
| `node:20-slim` | ~200MB | Production |
| `node:20-alpine` | ~130MB | Minimal |
| `alpine:3.18` | ~5MB | Minimal base |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic commands, pull, run, stop |
| **Mid** | Dockerfile, build images |
| **Mid-Senior** | Docker Compose, multi-service |
| **Senior** | Multi-stage, networking, volumes |
| **Expert** | Security, CI/CD, production |

**Golden Rules:**
- ✅ Use specific image versions
- ✅ Use multi-stage builds
- ✅ Use `.dockerignore`
- ✅ Run as non-root user
- ✅ Use health checks
- ✅ Limit resources
- ✅ Use named volumes for data
- ✅ Don't store secrets in images

**Development Workflow:**
```bash
# Start development
docker-compose up -d

# View logs
docker-compose logs -f web

# Run commands
docker-compose exec web python manage.py migrate

# Stop
docker-compose down
```
