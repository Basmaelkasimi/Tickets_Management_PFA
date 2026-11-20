# 🎫 Ticket Management System | DevOps & Cloud Project

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Containerization-blue?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-blue?logo=kubernetes)
![AWS](https://img.shields.io/badge/AWS-EKS-orange?logo=amazonaws)
![GitLab CI/CD](https://img.shields.io/badge/GitLab-CI%2FCD-orange?logo=gitlab)

## 📌 Project Overview

**Ticket Management System** is a web-based helpdesk application developed with Python and Flask to centralize and manage technical support requests.

The project combines **full-stack application development with DevOps and cloud engineering practices**, including Docker containerization, automated GitLab CI/CD pipelines, Kubernetes orchestration, and deployment to Amazon EKS.

### 🎯 Project Objectives

- Centralize IT support requests.
- Improve ticket tracking and assignment.
- Provide role-based interfaces for users, technicians, and administrators.
- Containerize the application using Docker.
- Automate application testing, image building, and deployment.
- Deploy and manage the application on AWS using Kubernetes.

---

## ✨ Key Features

### 👤 User
- Secure authentication
- Ticket creation and tracking
- Ticket history and comments
- Notifications
- Profile management

### 🛠️ Technician
- View assigned tickets
- Update ticket status
- Add comments and track interventions
- Access ticket history and notifications

### 👨‍💼 Administrator
- Dashboard and ticket overview
- Assign tickets to technicians
- Manage users, technicians, and categories
- Monitor ticket activity
- Access notifications and action history

---

## 🏗️ Architecture

```text
             Users / Technicians / Administrators
                            |
                            v
                    Flask Web Application
                            |
                            v
                     PostgreSQL Database
```

### DevOps & Cloud Architecture

```text
                 Source Code
                      |
                      v
                GitLab Repository
                      |
                      v
                 GitLab CI/CD
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
        TEST        BUILD       DEPLOY
          |           |           |
    Python Check   Docker      AWS EKS
                      |           |
                      v           v
                GitLab Registry  Kubernetes
                                   |
                                   v
                            Flask Application
                                   |
                                   v
                                PostgreSQL
```

---

## 🔄 CI/CD Pipeline

The project implements a three-stage GitLab CI/CD pipeline defined in `.gitlab-ci.yml`.

| Stage | Description | Technologies |
|---|---|---|
| Test | Install dependencies and validate Python source compilation | Python 3.13 |
| Build | Build and push a Docker image tagged with the commit SHA | Docker, GitLab Container Registry |
| Deploy | Update the Kubernetes deployment and verify rollout status | AWS EKS, Kubernetes, AWS CLI |

### Deployment Workflow

1. The CI/CD pipeline starts from the GitLab repository.
2. The test stage validates the Python source files.
3. Docker builds the application image.
4. The image is pushed to GitLab Container Registry.
5. The deployment job authenticates with AWS using GitLab OIDC and an IAM role.
6. Kubernetes updates the application image on Amazon EKS.
7. The pipeline checks the deployment rollout status.

**Note:** The deployment stage runs on the `main` branch.

---

## ☁️ AWS & Kubernetes Deployment

The application is configured for deployment on **Amazon Elastic Kubernetes Service (EKS)**.

Kubernetes manifests are available in the `k8s/` directory.

### Kubernetes Components

- **Deployment:** Runs the Flask application container.
- **Service:** Exposes the application through a LoadBalancer.
- **PostgreSQL Deployment:** Runs the database container.
- **PersistentVolumeClaim:** Provides persistent database storage.
- **Kubernetes Secrets references:** Supply application and database configuration without embedding secret values in the manifests.

The CI/CD pipeline uses **OIDC-based AWS authentication**, avoiding hardcoded AWS access keys in the pipeline configuration.

---

## 🐳 Docker Containerization

The project includes:

- `Dockerfile` for building the Flask application image.
- `compose.yaml` for running Flask and PostgreSQL together.
- `.dockerignore` to exclude unnecessary files from Docker builds.

### Local Setup

**Prerequisites:**
- Docker
- Docker Compose

**1. Clone the repository**

```bash
git clone https://github.com/Basmaelkasimi/Tickets_Management_PFA.git
cd Tickets_Management_PFA
```

**2. Configure environment variables**

Create a `.env` file based on `.env.example` and provide your own secure values.

Required Docker Compose variables include:

```env
SECRET_KEY=replace_with_a_long_random_secret
POSTGRES_DB=tickets
POSTGRES_USER=tickets_user
POSTGRES_PASSWORD=replace_with_a_strong_password
```

Never commit real credentials or secrets to Git.

**3. Start the application**

```bash
docker compose up --build -d
```

**4. Open the application**

```text
http://localhost:5000
```

**5. Stop the containers**

```bash
docker compose down
```

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, Jinja2 |
| Database | PostgreSQL, SQLAlchemy |
| Containerization | Docker, Docker Compose |
| CI/CD | GitLab CI/CD |
| Container Registry | GitLab Container Registry |
| Orchestration | Kubernetes |
| Cloud | AWS EKS |
| Authentication to AWS | OIDC, IAM |
| Version Control | Git, GitHub, GitLab |

---

## 📂 Project Structure

```text
Tickets_Management_PFA/
├── app.py
├── models.py
├── create_users.py
├── create_categories.py
├── migrate_sqlite_to_postgres.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
├── .gitlab-ci.yml
├── .env.example
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── postgres.yaml
│   └── postgres-pvc.yaml
├── assistant_ai/
├── static/
├── templates/
└── README.md
```

---

## 🔐 Security Practices

- Environment variables for sensitive application settings
- Kubernetes Secrets references for credentials
- GitLab OIDC authentication with AWS IAM
- No AWS access keys hardcoded in the CI/CD pipeline
- Separate configuration for local and cloud environments

---

## 🎓 Academic Context

This project was developed as part of an academic project (PFA), combining web application development, DevOps automation, and cloud deployment.

It demonstrates practical experience with:

- CI/CD pipeline configuration
- Docker image creation and registry management
- Kubernetes application deployment
- AWS EKS integration
- Cloud authentication and deployment automation

---

## 👩‍💻 Author

**Basma El Kasimi**

Master's Student — Networks and Information Systems

Interested in **DevOps Engineering, Cloud Computing, and Full-Stack Development**.

**GitHub:** [Basmaelkasimi](https://github.com/Basmaelkasimi)

---

⭐ If you find this project interesting, feel free to explore the repository!
