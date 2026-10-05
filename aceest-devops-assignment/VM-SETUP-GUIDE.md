# Complete Step-by-Step VM Guide
## DevOps Assignment — ACEest Fitness

> Do everything in this exact order. Each section builds on the previous one.

---

## PART 1: VM SETUP

### Step 1 — Update the system
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2 — Install Python 3.11
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
python3 --version   # should show 3.10+ (Ubuntu 22.04 ships 3.10, fine)
```

### Step 3 — Install Git
```bash
sudo apt install -y git
git --version
```

### Step 4 — Install Docker
```bash
# Remove old versions if any
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null

# Install prerequisites
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repo
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# Add your user to docker group (so you don't need sudo for docker)
sudo usermod -aG docker $USER
newgrp docker

# Test
docker run hello-world
```

### Step 5 — Install Jenkins
```bash
# Install Java (Jenkins requires it)
sudo apt install -y openjdk-17-jdk
java -version

# Add Jenkins repo
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y jenkins

# Start Jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins

# Get initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

> Open browser: **http://<your-VM-IP>:8080**
> Paste the password, click "Install Suggested Plugins", create your admin account.

### Step 6 — Give Jenkins access to Docker
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

---

## PART 2: GITHUB SETUP

### Step 1 — Create GitHub account
Go to https://github.com and sign up (or log in).

### Step 2 — Create a new public repository
1. Click **+** → **New repository**
2. Name: `aceest-devops`
3. Set to **Public**
4. Do NOT initialize with README (we'll push our own)
5. Click **Create repository**

### Step 3 — Configure Git on the VM
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### Step 4 — Set up SSH key for GitHub (recommended)
```bash
# Generate key
ssh-keygen -t ed25519 -C "your@email.com"
# Press Enter 3 times (accept defaults, no passphrase)

# Copy the public key
cat ~/.ssh/id_ed25519.pub
```
Go to GitHub → Settings → SSH and GPG Keys → **New SSH Key** → paste it → Save.

Test: `ssh -T git@github.com` (should say "Hi username!")

---

## PART 3: PROJECT SETUP & GIT VERSIONING

### Step 1 — Create project folder on VM
```bash
mkdir ~/aceest-devops
cd ~/aceest-devops
```

### Step 2 — Copy all project files to VM

**Option A — transfer from your Mac via SCP:**
```bash
# Run this on your Mac (not the VM)
scp -r /Users/I572550/Downloads/aceest-devops-assignment/* user@<VM-IP>:~/aceest-devops/
```

**Option B — create files directly on VM** by copying the content from each file.

### Step 3 — Initialize Git repository
```bash
cd ~/aceest-devops
git init
git remote add origin git@github.com:<YOUR-USERNAME>/aceest-devops.git
```

### Step 4 — Commit versions following the assignment versioning strategy

Each version from the code folder maps to a meaningful commit:

```bash
# Version 1.0 - Basic Flask app skeleton
git add app.py templates/ requirements.txt
git commit -m "feat: initial Flask app - ACEest fitness management v1.0

- Login system with session management
- Dashboard showing all clients
- Three fitness programs: Fat Loss, Muscle Gain, Beginner"

# Version 1.1 - Client management
git add .
git commit -m "feat: client CRUD operations v1.1

- Add client form with age, height, weight, program
- Calorie calculator (weight x program factor)
- Membership tracking"

# Version 2.0 - DevOps infrastructure
git add Dockerfile .github/ Jenkinsfile
git commit -m "feat: DevOps infrastructure v2.0

- Dockerfile with multi-stage build and non-root user
- GitHub Actions CI/CD pipeline (lint -> test -> docker)
- Jenkinsfile for secondary BUILD environment"

# Version 2.1 - Test suite
git add test_app.py
git commit -m "test: comprehensive pytest suite v2.1

- Unit tests: calorie calculation, program validation
- Integration tests: all routes, auth, DB operations
- Coverage reporting"

# Version 3.0 - Documentation
git add README.md
git commit -m "docs: professional README with setup and architecture v3.0

- Local setup instructions
- Manual test execution steps
- GitHub Actions and Jenkins integration overview"
```

### Step 5 — Push to GitHub
```bash
git branch -M main
git push -u origin main
```

### Step 6 — Verify on GitHub
Open your GitHub repo. You should see all files and commit history.

---

## PART 4: VERIFY THE APPLICATION LOCALLY ON VM

```bash
cd ~/aceest-devops

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize DB and run
python app.py
```

> App runs at http://localhost:5000 (or http://<VM-IP>:5000 from browser)
> Login: admin / admin123

---

## PART 5: RUN TESTS ON VM

```bash
cd ~/aceest-devops
source venv/bin/activate

# Run tests
pytest test_app.py -v

# With coverage
pytest test_app.py -v --cov=app --cov-report=term-missing
```

Expected: all 14+ tests pass, ~80%+ coverage.

---

## PART 6: DOCKER ON VM

```bash
cd ~/aceest-devops

# Build image
docker build -t aceest-fitness:latest .

# Verify image was created
docker images | grep aceest

# Run container
docker run -d --name aceest -p 5000:5000 aceest-fitness:latest

# Check it's running
docker ps
curl http://localhost:5000/health

# View logs
docker logs aceest

# Run tests inside container
docker run --rm aceest-fitness:latest pytest test_app.py -v

# Stop and clean up
docker stop aceest && docker rm aceest
```

---

## PART 7: GITHUB ACTIONS — VERIFY PIPELINE

### How it works
Every time you `git push` to `main`, GitHub automatically:
1. Runs `flake8` lint check
2. Runs `pytest` test suite
3. Builds Docker image
4. Runs `/health` smoke test on the container

### How to trigger it
```bash
# Make any small change, commit and push
echo "# test" >> README.md
git add README.md
git commit -m "ci: trigger pipeline test"
git push
```

### How to see results
1. Go to your GitHub repo
2. Click the **Actions** tab
3. Click the latest run
4. Green checkmarks = all passed ✓

---

## PART 8: JENKINS SETUP

### Step 1 — Open Jenkins
Go to **http://<VM-IP>:8080** in your browser.

### Step 2 — Create a Pipeline Job
1. Click **New Item**
2. Name: `aceest-fitness`
3. Select **Pipeline** → Click OK
4. Scroll to **Pipeline** section
5. Definition: select **Pipeline script from SCM**
6. SCM: **Git**
7. Repository URL: `https://github.com/<YOUR-USERNAME>/aceest-devops.git`
8. Branch: `*/main`
9. Script Path: `Jenkinsfile`
10. Click **Save**

### Step 3 — Run the Jenkins Build
1. Click **Build Now**
2. Click the build number under "Build History"
3. Click **Console Output** to watch it run

### Step 4 — Set up Webhook (auto-trigger on push)
1. Go to your GitHub repo → **Settings** → **Webhooks** → **Add webhook**
2. Payload URL: `http://<VM-IP>:8080/github-webhook/`
3. Content type: `application/json`
4. Events: select **Just the push event**
5. Click **Add webhook**

Back in Jenkins:
1. Open your job → **Configure**
2. Under **Build Triggers**, check **GitHub hook trigger for GITScm polling**
3. Save

Now every `git push` triggers both GitHub Actions AND Jenkins automatically.

---

## PART 9: UPDATE JENKINSFILE WITH YOUR REPO URL

Edit `Jenkinsfile` on the VM:
```bash
nano ~/aceest-devops/Jenkinsfile
```
Replace `<YOUR-USERNAME>` with your actual GitHub username, then:
```bash
git add Jenkinsfile
git commit -m "config: update Jenkins git URL with actual repo"
git push
```

---

## PART 10: WHAT TO SUBMIT

Your submission is your **public GitHub repository link**.

Make sure it contains:
- [ ] `app.py` — Flask application
- [ ] `requirements.txt` — dependencies
- [ ] `test_app.py` — pytest test suite
- [ ] `Dockerfile` — container definition
- [ ] `Jenkinsfile` — Jenkins pipeline
- [ ] `.github/workflows/main.yml` — GitHub Actions
- [ ] `templates/` — all HTML templates
- [ ] `README.md` — documentation
- [ ] GitHub Actions **green** (all checks passing) ✓
- [ ] Meaningful commit history with multiple commits ✓

---

## QUICK REFERENCE — Commands Cheat Sheet

| Task | Command |
|---|---|
| Activate venv | `source venv/bin/activate` |
| Run app | `python app.py` |
| Run tests | `pytest test_app.py -v` |
| Build Docker | `docker build -t aceest-fitness .` |
| Run Docker | `docker run -p 5000:5000 aceest-fitness` |
| Git status | `git status` |
| Git commit | `git add . && git commit -m "message"` |
| Git push | `git push` |
| Check Jenkins | `sudo systemctl status jenkins` |
| Jenkins password | `sudo cat /var/lib/jenkins/secrets/initialAdminPassword` |
