# ACEest Fitness & Gym — DevOps Assignment

> **Course:** Introduction to DevOps (CSIZG514/SEZG514) | S1-2026
> **Application:** ACEest Functional Fitness Management System

---

## Table of Contents
1. [Application Overview](#application-overview)
2. [Local Setup](#local-setup)
3. [Running Tests Manually](#running-tests-manually)
4. [Docker](#docker)
5. [GitHub Actions Pipeline](#github-actions-pipeline)
6. [Jenkins Integration](#jenkins-integration)

---

## Application Overview

ACEest is a Flask-based fitness gym management web application. Features:

- Role-based login (Admin / Trainer)
- Client management with program assignment
- Calorie calculator based on weight × program factor
- Weekly adherence progress tracking
- Workout logging and body metrics
- AI-style program generation
- REST health check endpoint (`/health`)

**Default credentials:** `admin` / `admin123`

---

## Local Setup

### Prerequisites
- Python 3.11+
- pip
- (Optional) Docker

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/aceest-devops.git
cd aceest-devops

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Running Tests Manually

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest test_app.py -v

# Run tests with coverage report
pytest test_app.py -v --cov=app --cov-report=term-missing

# Run a specific test
pytest test_app.py::test_calculate_calories_fat_loss -v
```

Expected output: all tests pass with ~80%+ coverage.

---

## Docker

### Build the image

```bash
docker build -t aceest-fitness:latest .
```

### Run the container

```bash
docker run -d \
  --name aceest \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  aceest-fitness:latest
```

Open: **http://localhost:5000**

### Run tests inside container

```bash
docker run --rm aceest-fitness:latest pytest test_app.py -v
```

### Stop and remove

```bash
docker stop aceest && docker rm aceest
```

---

## GitHub Actions Pipeline

The pipeline is defined in `.github/workflows/main.yml` and triggers on every `push` or `pull_request` to `main`.

### Pipeline Stages

```
Push / PR
    │
    ▼
┌─────────┐     ┌──────────┐     ┌──────────────┐
│  Lint   │────▶│  Pytest  │────▶│ Docker Build │
│ flake8  │     │ + Cover  │     │ + Smoke Test │
└─────────┘     └──────────┘     └──────────────┘
```

| Stage | What it does |
|---|---|
| **Lint** | Runs `flake8` to catch syntax errors and style issues |
| **Test** | Runs full `pytest` suite with coverage report |
| **Docker Build** | Builds the Docker image and runs a `/health` smoke test |

**Each stage only runs if the previous one passes.** A failed test blocks the Docker build.

### Viewing results
1. Go to your GitHub repo → **Actions** tab
2. Click the latest workflow run
3. Expand each job to see logs

---

## Jenkins Integration

### Purpose
Jenkins provides a secondary BUILD environment — it pulls the latest code from GitHub and performs a clean build, acting as a quality gate independent of GitHub Actions.

### Jenkins Pipeline Logic

```
GitHub Push
    │
    ▼
Jenkins Webhook
    │
    ▼
┌──────────────────────────────────┐
│  Stage 1: Checkout from GitHub   │
│  Stage 2: Install dependencies   │
│  Stage 3: Run Pytest             │
│  Stage 4: Build Docker image     │
└──────────────────────────────────┘
```

### Jenkinsfile

```groovy
pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/<your-username>/aceest-devops.git'
            }
        }
        stage('Install') {
            steps {
                sh 'pip3 install -r requirements.txt'
            }
        }
        stage('Test') {
            steps {
                sh 'pytest test_app.py -v --tb=short'
            }
        }
        stage('Docker Build') {
            steps {
                sh 'docker build -t aceest-fitness:jenkins-build .'
            }
        }
    }
    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo 'BUILD SUCCESSFUL — all stages passed.'
        }
        failure {
            echo 'BUILD FAILED — check logs above.'
        }
    }
}
```

---

## Project Structure

```
aceest-devops/
├── app.py                          # Flask application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container definition
├── test_app.py                     # Pytest test suite
├── Jenkinsfile                     # Jenkins pipeline
├── README.md                       # This file
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── add_client.html
│   ├── client_profile.html
│   └── add_user.html
└── .github/
    └── workflows/
        └── main.yml                # GitHub Actions CI/CD
```
