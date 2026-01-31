# 🔀 GIT - Version Control (Junior → Senior)

Dokumentasi lengkap Git untuk backend developer dari basic hingga advanced workflows.

---

## 🎯 Kenapa Harus Git?

**Tanpa Git:**
```
project_final.zip
project_final_v2.zip
project_final_v2_fix.zip
project_final_v2_fix_REAL.zip
project_final_v2_fix_REAL_banget.zip  😱
```

**Dengan Git:**
```
commit 1: Initial project setup
commit 2: Add user authentication
commit 3: Fix login bug
commit 4: Add task CRUD
commit 5: Refactor API responses
```

---

## 1️⃣ JUNIOR LEVEL - Git Basics

### Install Git

```bash
# Linux
sudo apt install git

# Mac
brew install git

# Windows
# Download dari https://git-scm.com/
```

### Initial Setup

```bash
# Set identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Check config
git config --list
```

### Create Repository

```bash
# Initialize new repo
cd my-project
git init

# Clone existing repo
git clone https://github.com/username/repo.git
git clone git@github.com:username/repo.git  # SSH
```

### Basic Workflow

```bash
# 1. Check status
git status

# 2. Add files to staging
git add filename.py        # Single file
git add .                  # All files
git add *.py               # All Python files
git add src/               # All files in folder

# 3. Commit changes
git commit -m "Add user login feature"

# 4. Push to remote
git push origin main
```

### View History

```bash
# View commit history
git log
git log --oneline          # Compact view
git log --graph            # With branch graph
git log -5                 # Last 5 commits

# View specific commit
git show abc1234

# View file changes
git diff                   # Unstaged changes
git diff --staged          # Staged changes
git diff HEAD~1            # Compare with previous commit
```

---

## 2️⃣ MID LEVEL - Branching

### Branch Concept

```
main ────●────●────●────●────●
              │              ↑
              └──●──●──●─────┘
              feature-branch
```

### Branch Commands

```bash
# List branches
git branch                 # Local branches
git branch -a              # All branches (including remote)

# Create branch
git branch feature-login

# Switch branch
git checkout feature-login
git switch feature-login   # New syntax (Git 2.23+)

# Create and switch
git checkout -b feature-login
git switch -c feature-login

# Delete branch
git branch -d feature-login      # Safe delete
git branch -D feature-login      # Force delete
```

### Merge Branches

```bash
# Switch to target branch
git checkout main

# Merge feature branch
git merge feature-login

# Merge with commit message
git merge feature-login -m "Merge: Add login feature"
```

### Merge Conflicts

```python
# Conflict example in file:
<<<<<<< HEAD
def login(username, password):
    # Current branch code
=======
def login(email, password):
    # Incoming branch code
>>>>>>> feature-login
```

**Resolve:**
```bash
# 1. Edit file manually, choose correct code
def login(email, password):
    # Fixed code

# 2. Add resolved file
git add filename.py

# 3. Complete merge
git commit -m "Resolve merge conflict"
```

---

## 3️⃣ MID-SENIOR LEVEL - Git Workflows

### A) Git Flow

```
main ─────●───────────────────────────●─────
          │                           ↑
develop ──●──●──●──●──●──●──●──●──●──●─────
             │     ↑     │        ↑
feature ─────●──●──┘     │        │
                         │        │
hotfix ──────────────────●────────┘
```

**Branches:**
- `main` - Production code
- `develop` - Integration branch
- `feature/*` - New features
- `release/*` - Release preparation
- `hotfix/*` - Production fixes

```bash
# Start feature
git checkout develop
git checkout -b feature/user-auth

# Work on feature
git add .
git commit -m "Add login endpoint"

# Finish feature
git checkout develop
git merge feature/user-auth
git branch -d feature/user-auth

# Create release
git checkout -b release/1.0.0
# Test, fix bugs
git checkout main
git merge release/1.0.0
git tag v1.0.0

# Hotfix
git checkout main
git checkout -b hotfix/login-bug
# Fix bug
git checkout main
git merge hotfix/login-bug
git checkout develop
git merge hotfix/login-bug
```

### B) GitHub Flow (Simpler)

```
main ────●────●────●────●────●────●
         │    ↑    │    ↑    │    ↑
         └────┘    └────┘    └────┘
         PR #1     PR #2     PR #3
```

**Workflow:**
```bash
# 1. Create branch from main
git checkout main
git pull
git checkout -b feature/new-api

# 2. Work on feature
git add .
git commit -m "Add new API endpoint"
git push origin feature/new-api

# 3. Open Pull Request on GitHub
# 4. Code review
# 5. Merge via GitHub UI
# 6. Delete branch
```

### C) Trunk-Based Development

```
main ─●─●─●─●─●─●─●─●─●─●─●─●─●
      ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
      Small commits directly to main
```

**Workflow:**
```bash
# Small, frequent commits to main
git checkout main
git pull
# Make small change
git add .
git commit -m "Fix typo in API response"
git push origin main
```

---

## 4️⃣ SENIOR LEVEL - Advanced Commands

### Stash (Save Work Temporarily)

```bash
# Save current work
git stash
git stash save "WIP: login feature"

# List stashes
git stash list

# Apply stash
git stash pop              # Apply and delete
git stash apply            # Apply and keep
git stash apply stash@{2}  # Apply specific

# Delete stash
git stash drop stash@{0}
git stash clear            # Delete all
```

### Rebase (Clean History)

```bash
# Rebase feature on main
git checkout feature-branch
git rebase main

# Interactive rebase (squash commits)
git rebase -i HEAD~3

# In editor:
pick abc1234 First commit
squash def5678 Second commit
squash ghi9012 Third commit

# Abort rebase
git rebase --abort
```

### Cherry Pick (Copy Commits)

```bash
# Copy specific commit to current branch
git cherry-pick abc1234

# Copy multiple commits
git cherry-pick abc1234 def5678

# Cherry pick without commit
git cherry-pick abc1234 --no-commit
```

### Reset & Revert

```bash
# Soft reset (keep changes staged)
git reset --soft HEAD~1

# Mixed reset (keep changes unstaged)
git reset HEAD~1

# Hard reset (discard all changes) ⚠️
git reset --hard HEAD~1

# Revert commit (create new commit that undoes)
git revert abc1234
```

### Reflog (Recovery)

```bash
# View all actions
git reflog

# Recover deleted branch/commit
git checkout -b recovered-branch abc1234
```

---

## 5️⃣ SENIOR LEVEL - Remote Operations

### Remote Management

```bash
# List remotes
git remote -v

# Add remote
git remote add origin https://github.com/user/repo.git
git remote add upstream https://github.com/original/repo.git

# Remove remote
git remote remove origin

# Change remote URL
git remote set-url origin git@github.com:user/repo.git
```

### Fetch vs Pull

```bash
# Fetch: Download without merge
git fetch origin
git fetch --all

# Pull: Fetch + Merge
git pull origin main

# Pull with rebase
git pull --rebase origin main
```

### Push Options

```bash
# Push to remote
git push origin main

# Push new branch
git push -u origin feature-branch

# Force push (careful!) ⚠️
git push --force origin main
git push --force-with-lease origin main  # Safer

# Push tags
git push origin v1.0.0
git push origin --tags
```

### Sync Fork

```bash
# Add upstream (original repo)
git remote add upstream https://github.com/original/repo.git

# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

---

## 6️⃣ EXPERT LEVEL - Git Hooks

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Run linter before commit
echo "Running linter..."
flake8 .

if [ $? -ne 0 ]; then
    echo "❌ Linting failed! Fix errors before commit."
    exit 1
fi

echo "✅ Linting passed!"
```

### Pre-push Hook

```bash
# .git/hooks/pre-push
#!/bin/bash

# Run tests before push
echo "Running tests..."
python -m pytest

if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Fix before pushing."
    exit 1
fi

echo "✅ Tests passed!"
```

### Using Husky (Node.js)

```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged",
      "pre-push": "npm test"
    }
  }
}
```

---

## 7️⃣ EXPERT LEVEL - Git Best Practices

### Commit Messages

```bash
# ✅ Good commit messages
git commit -m "Add user authentication with JWT"
git commit -m "Fix: Login fails with special characters"
git commit -m "Refactor: Extract validation to service layer"

# ❌ Bad commit messages
git commit -m "fix"
git commit -m "update"
git commit -m "asdfasdf"
git commit -m "WIP"
```

### Conventional Commits

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructure
- `test:` Add tests
- `chore:` Maintenance

```bash
git commit -m "feat(auth): add JWT refresh token"
git commit -m "fix(api): handle null response"
git commit -m "docs: update API documentation"
git commit -m "refactor(db): optimize query performance"
```

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
venv/
.env

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
logs/
node_modules/
dist/
build/
*.sqlite3
```

### Git Aliases

```bash
# Add aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --all"
git config --global alias.last "log -1 HEAD"

# Usage
git co main
git br -a
git lg
```

---

## 📊 Command Reference

### Most Used Commands

| Command | Description |
|---------|-------------|
| `git init` | Initialize repo |
| `git clone <url>` | Clone repo |
| `git add .` | Stage all files |
| `git commit -m "msg"` | Commit changes |
| `git push` | Push to remote |
| `git pull` | Pull from remote |
| `git status` | Check status |
| `git log` | View history |
| `git branch` | List branches |
| `git checkout -b <name>` | Create & switch branch |
| `git merge <branch>` | Merge branch |
| `git stash` | Save work temporarily |

### Danger Zone ⚠️

| Command | Risk | Use Case |
|---------|------|----------|
| `git reset --hard` | 🔴 Lose changes | Discard all local changes |
| `git push --force` | 🔴 Overwrite history | After rebase (careful!) |
| `git clean -fd` | 🔴 Delete files | Remove untracked files |
| `git checkout -- .` | 🟡 Lose unstaged | Discard unstaged changes |

---

## 🎯 Workflow Comparison

| Workflow | Complexity | Team Size | Best For |
|----------|-----------|-----------|----------|
| **GitHub Flow** | 🟢 Simple | 1-5 | Small teams, fast releases |
| **Git Flow** | 🔴 Complex | 5-20 | Scheduled releases |
| **Trunk-Based** | 🟢 Simple | Any | CI/CD, experienced teams |

---

## 💡 Summary

| Level | Skills |
|-------|--------|
| **Junior** | init, add, commit, push, pull, status |
| **Mid** | branch, merge, resolve conflicts |
| **Mid-Senior** | Git Flow, GitHub Flow, PRs |
| **Senior** | stash, rebase, cherry-pick, reflog |
| **Expert** | hooks, aliases, advanced workflows |

**Golden Rules:**
- ✅ Commit often, push daily
- ✅ Write meaningful commit messages
- ✅ Always pull before push
- ✅ Never commit to main directly
- ✅ Use branches for features
- ✅ Review code before merge
- ⚠️ Be careful with force push
- ⚠️ Don't commit secrets/passwords

**Daily Workflow:**
```bash
# Morning
git checkout main
git pull

# Start work
git checkout -b feature/my-task

# During day
git add .
git commit -m "feat: implement feature"

# End of day
git push origin feature/my-task
# Create PR if ready
```
