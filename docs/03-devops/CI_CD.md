# 🔄 CI/CD - Continuous Integration & Deployment (Junior → Senior)

Dokumentasi lengkap tentang CI/CD dari basic concepts hingga advanced deployment strategies.

---

## 🎯 Apa itu CI/CD?

```
┌─────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│  Push    →   Build   →   Test   →   Deploy   →   Monitor      │
│  Code        App         All        Auto          Check        │
│                          Tests      Deploy        Health       │
└─────────────────────────────────────────────────────────────────┘

CI = Continuous Integration
- Merge code frequently
- Automated build & test
- Fast feedback

CD = Continuous Delivery/Deployment
- Automated deployment to staging
- One-click production deploy (Delivery)
- Auto deploy to production (Deployment)
```

**Benefits:**
- ✅ Faster release cycles
- ✅ Early bug detection
- ✅ Consistent deployments
- ✅ Less human error
- ✅ Better collaboration

---

## 1️⃣ JUNIOR LEVEL - CI/CD Basics

### Pipeline Concepts

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Source  │ → │  Build   │ → │   Test   │ → │  Deploy  │
│  (Git)   │   │  (App)   │   │ (pytest) │   │ (Server) │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │
   Push          Compile      Run tests     If tests
   code          /Bundle      Lint/Type     pass
```

### Basic GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest
```

### Understanding Workflow File

```yaml
# Workflow name (shown in GitHub UI)
name: CI

# When to run
on:
  push:             # On push to branches
    branches: [main]
  pull_request:     # On PR to branches
    branches: [main]
  schedule:         # Cron schedule
    - cron: '0 0 * * *'  # Daily at midnight

# Jobs to run
jobs:
  job-name:
    runs-on: ubuntu-latest  # Runner OS
    
    steps:
      - name: Step description
        uses: action/name@version  # Use existing action
        
      - name: Run command
        run: |
          echo "Hello"
          echo "World"
```

---

## 2️⃣ MID LEVEL - Real CI Pipelines

### Python Django CI

```yaml
# .github/workflows/django-ci.yml
name: Django CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install linters
        run: pip install flake8 black isort
      
      - name: Run flake8
        run: flake8 .
      
      - name: Check black formatting
        run: black --check .
      
      - name: Check import order
        run: isort --check-only .

  test:
    runs-on: ubuntu-latest
    needs: lint  # Run after lint passes
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'  # Cache pip packages
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run migrations
        run: python manage.py migrate
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
      
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Node.js CI

```yaml
# .github/workflows/node-ci.yml
name: Node.js CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18.x, 20.x]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build
```

### Go CI

```yaml
# .github/workflows/go-ci.yml
name: Go CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
          cache: true
      
      - name: Install dependencies
        run: go mod download
      
      - name: Run golangci-lint
        uses: golangci/golangci-lint-action@v3
      
      - name: Run tests
        run: go test -v -race -coverprofile=coverage.out ./...
      
      - name: Build
        run: go build -v ./...
```

---

## 3️⃣ MID-SENIOR LEVEL - CD Pipelines

### Deploy to VPS/Server

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  deploy:
    runs-on: ubuntu-latest
    needs: test  # Only deploy if tests pass
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/myapp
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            sudo systemctl restart myapp
```

### Docker Build & Push

```yaml
# .github/workflows/docker-deploy.yml
name: Docker Deploy

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: myuser/myapp
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix=
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Deploy to Cloud (AWS ECS)

```yaml
# .github/workflows/aws-deploy.yml
name: AWS Deploy

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: myapp
  ECS_SERVICE: myapp-service
  ECS_CLUSTER: myapp-cluster

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment
```

---

## 4️⃣ SENIOR LEVEL - Advanced Patterns

### Environment-Based Deploy

```yaml
# .github/workflows/deploy-environments.yml
name: Deploy to Environments

on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # Deploy script here

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # Deploy script here
```

### Reusable Workflows

```yaml
# .github/workflows/reusable-test.yml
name: Reusable Test

on:
  workflow_call:
    inputs:
      python-version:
        required: true
        type: string
    secrets:
      CODECOV_TOKEN:
        required: false

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ inputs.python-version }}
      
      - name: Run tests
        run: pytest


# .github/workflows/main.yml (calling reusable workflow)
name: Main CI

on: [push]

jobs:
  call-tests:
    uses: ./.github/workflows/reusable-test.yml
    with:
      python-version: '3.11'
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### Matrix Strategy

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false  # Don't cancel other jobs if one fails
      matrix:
        python-version: ['3.9', '3.10', '3.11']
        database: ['postgres', 'mysql']
        include:
          - python-version: '3.11'
            database: 'postgres'
            experimental: true
        exclude:
          - python-version: '3.9'
            database: 'mysql'
    
    steps:
      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Test with ${{ matrix.database }}
        run: |
          echo "Testing Python ${{ matrix.python-version }} with ${{ matrix.database }}"
```

---

## 5️⃣ SENIOR LEVEL - Deployment Strategies

### Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
│                         │                                │
│           ┌─────────────┼─────────────┐                  │
│           ▼             │             ▼                  │
│    ┌──────────┐         │      ┌──────────┐             │
│    │   Blue   │ ◄───────┘      │   Green  │             │
│    │  (Live)  │                │  (Idle)  │             │
│    │   v1.0   │                │   v1.1   │             │
│    └──────────┘                └──────────┘             │
└─────────────────────────────────────────────────────────┘

1. Deploy new version to Green
2. Test Green environment
3. Switch traffic from Blue to Green
4. Blue becomes the new idle (rollback target)
```

```yaml
# GitHub Actions Blue-Green example
- name: Deploy to Green
  run: |
    aws ecs update-service \
      --cluster myapp-cluster \
      --service myapp-green \
      --task-definition myapp:${{ github.sha }}

- name: Health check Green
  run: |
    for i in {1..30}; do
      if curl -f https://green.myapp.com/health; then
        echo "Green is healthy"
        exit 0
      fi
      sleep 10
    done
    exit 1

- name: Switch traffic to Green
  run: |
    aws elbv2 modify-listener \
      --listener-arn $LISTENER_ARN \
      --default-actions Type=forward,TargetGroupArn=$GREEN_TARGET_GROUP
```

### Canary Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
│                         │                                │
│         ┌───────────────┼───────────────┐                │
│         │ 90%           │           10% │                │
│         ▼               │               ▼                │
│    ┌──────────┐         │        ┌──────────┐           │
│    │  Stable  │         │        │  Canary  │           │
│    │   v1.0   │         │        │   v1.1   │           │
│    │ (9 pods) │         │        │ (1 pod)  │           │
│    └──────────┘         │        └──────────┘           │
└─────────────────────────────────────────────────────────┘

1. Deploy new version to small % of traffic
2. Monitor errors/performance
3. Gradually increase traffic %
4. Full rollout or rollback
```

```yaml
# Canary with percentages
- name: Deploy canary (10%)
  run: |
    kubectl set image deployment/myapp-canary app=myapp:${{ github.sha }}
    kubectl scale deployment/myapp-canary --replicas=1
    kubectl scale deployment/myapp-stable --replicas=9

- name: Monitor canary
  run: |
    sleep 300  # Wait 5 minutes
    ERROR_RATE=$(curl -s prometheus/api/v1/query?query=error_rate | jq .data.result[0].value[1])
    if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
      echo "Error rate too high, rolling back"
      kubectl scale deployment/myapp-canary --replicas=0
      exit 1
    fi

- name: Full rollout
  run: |
    kubectl set image deployment/myapp-stable app=myapp:${{ github.sha }}
    kubectl scale deployment/myapp-canary --replicas=0
```

### Rolling Deployment

```
┌─────────────────────────────────────────────────────────┐
│  Step 1:  [v1] [v1] [v1] [v1] [v1]                      │
│  Step 2:  [v2] [v1] [v1] [v1] [v1]                      │
│  Step 3:  [v2] [v2] [v1] [v1] [v1]                      │
│  Step 4:  [v2] [v2] [v2] [v1] [v1]                      │
│  Step 5:  [v2] [v2] [v2] [v2] [v1]                      │
│  Step 6:  [v2] [v2] [v2] [v2] [v2]                      │
└─────────────────────────────────────────────────────────┘

- Gradual replacement
- Zero downtime
- Easy rollback
```

---

## 6️⃣ SENIOR LEVEL - Secrets Management

### GitHub Secrets

```yaml
# Using secrets in workflow
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    ./deploy.sh

# Environment-specific secrets
- name: Deploy to production
  environment: production
  env:
    API_KEY: ${{ secrets.PROD_API_KEY }}  # From production environment
```

### Secret Rotation

```yaml
# Rotate secrets periodically
name: Rotate Secrets

on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly

jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - name: Generate new API key
        id: new-key
        run: |
          NEW_KEY=$(openssl rand -hex 32)
          echo "::add-mask::$NEW_KEY"
          echo "key=$NEW_KEY" >> $GITHUB_OUTPUT
      
      - name: Update application
        run: |
          # Update the key in your application
          aws ssm put-parameter \
            --name /myapp/api-key \
            --value ${{ steps.new-key.outputs.key }} \
            --overwrite
```

---

## 7️⃣ EXPERT LEVEL - GitLab CI/CD

### Basic GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

build:
  stage: build
  image: python:3.11
  script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install -r requirements.txt
  artifacts:
    paths:
      - venv/

test:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    DATABASE_URL: postgres://postgres:postgres@postgres:5432/test_db
  script:
    - source venv/bin/activate
    - pytest --cov=.
  needs:
    - build

deploy_staging:
  stage: deploy
  script:
    - ./deploy.sh staging
  environment:
    name: staging
    url: https://staging.myapp.com
  only:
    - develop

deploy_production:
  stage: deploy
  script:
    - ./deploy.sh production
  environment:
    name: production
    url: https://myapp.com
  only:
    - main
  when: manual  # Require manual trigger
```

---

## 8️⃣ EXPERT LEVEL - Monitoring & Notifications

### Slack Notifications

```yaml
- name: Notify Slack on success
  if: success()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    payload: |
      {
        "text": "✅ Deployment successful!",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Deployment successful!*\n• Branch: `${{ github.ref_name }}`\n• Commit: `${{ github.sha }}`"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    payload: |
      {
        "text": "❌ Deployment failed!",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Deployment failed!*\n• Branch: `${{ github.ref_name }}`\n• <${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View logs>"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Status Checks

```yaml
# Require status checks before merge
# In GitHub repo settings:
# Settings → Branches → Branch protection rules
# - Require status checks to pass
# - Require branches to be up to date

# Make jobs required
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
  
  # This job summarizes all checks
  all-checks:
    if: always()
    needs: [test, lint, build]
    runs-on: ubuntu-latest
    steps:
      - name: Check all jobs passed
        run: |
          if [[ "${{ needs.test.result }}" != "success" ]] || \
             [[ "${{ needs.lint.result }}" != "success" ]] || \
             [[ "${{ needs.build.result }}" != "success" ]]; then
            exit 1
          fi
```

---

## 📊 Quick Reference

### GitHub Actions vs GitLab CI

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| Config File | `.github/workflows/*.yml` | `.gitlab-ci.yml` |
| Stages | `jobs:` | `stages:` |
| Dependencies | `needs:` | `needs:` |
| Environment | `environment:` | `environment:` |
| Secrets | Settings → Secrets | Settings → CI/CD → Variables |
| Matrix | `strategy.matrix` | `parallel:matrix` |
| Manual trigger | `workflow_dispatch` | `when: manual` |

### Common Actions

| Action | Purpose |
|--------|---------|
| `actions/checkout@v4` | Checkout code |
| `actions/setup-python@v4` | Setup Python |
| `actions/setup-node@v4` | Setup Node.js |
| `docker/build-push-action@v5` | Build/push Docker |
| `aws-actions/configure-aws-credentials@v4` | AWS auth |
| `appleboy/ssh-action@v1` | SSH to server |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic workflows, run tests on push |
| **Mid** | Services (DB, Redis), caching, coverage |
| **Mid-Senior** | Deploy to servers, Docker push |
| **Senior** | Blue-Green, Canary, secrets |
| **Expert** | Multi-environment, monitoring |

**Best Practices:**
- ✅ Run tests on every push
- ✅ Use caching for faster builds
- ✅ Require status checks for merge
- ✅ Use environment protection rules
- ✅ Never store secrets in code
- ✅ Notify team on failures
- ✅ Use deployment strategies (not direct push)
- ✅ Monitor after deploy

**Minimal CI Pipeline:**
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
```
