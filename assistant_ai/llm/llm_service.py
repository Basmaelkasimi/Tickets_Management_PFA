import os
import re
from google import genai


# =========================================================
# CONFIGURATION GEMINI
# =========================================================

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError(
        "La variable GEMINI_API_KEY n'est pas configurée."
    )

client = genai.Client()

MODEL = "gemini-2.5-flash"


# =========================================================
# FONCTION UTILITAIRE
# Nettoie les ```dockerfile, ```yaml, etc.
# =========================================================

def clean_generated_content(content):
    if not content:
        return ""

    content = content.strip()

    content = re.sub(
        r"^```(?:dockerfile|yaml|yml|text|bash)?\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(r"\s*```$", "", content)

    return content.strip()


# =========================================================
# 1. GENERATION DOCKERFILE
# =========================================================

def generate_dockerfile(language, framework, port, requirements_file):

    prompt = f"""
Tu es un ingénieur DevOps expert.

Génère un Dockerfile adapté au projet suivant :

Langage : {language}
Framework : {framework}
Port : {port}
Fichier de dépendances : {requirements_file}

Contraintes :
- utiliser une image de base légère
- définir un WORKDIR
- installer correctement les dépendances
- copier le code de l'application
- exposer le port {port}
- démarrer correctement l'application
- suivre les bonnes pratiques Docker
- ne fournir aucune explication
- retourner uniquement le contenu du Dockerfile
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return clean_generated_content(response.text)


# =========================================================
# 2. GENERATION DOCKER COMPOSE
# =========================================================

def generate_docker_compose(
    application_name,
    port,
    container_port
):
    prompt = f"""
Tu es un ingénieur DevOps expert.

Génère un fichier compose.yaml adapté à une application Flask
utilisant PostgreSQL.

Nom de l'application : {application_name}
Port hôte : {port}
Port du conteneur Flask : {container_port}

Le fichier doit contenir deux services :

1. db
- image postgres:17
- variables :
  POSTGRES_DB
  POSTGRES_USER
  POSTGRES_PASSWORD
- volume postgres_data
- healthcheck avec pg_isready

2. web
- build: .
- mapper le port {port}:{container_port}
- variables :
  DATABASE_URL
  SECRET_KEY
- DATABASE_URL doit utiliser le service db
- depends_on doit attendre que db soit healthy

Contraintes :
- syntaxe Docker Compose moderne
- ne jamais écrire de mot de passe directement
- utiliser les variables ${{POSTGRES_DB}}, ${{POSTGRES_USER}},
  ${{POSTGRES_PASSWORD}} et ${{SECRET_KEY}}
- définir le volume postgres_data

- DATABASE_URL doit commencer par postgresql+psycopg://
- terminer obligatoirement le fichier par :
  volumes:
    postgres_data:
- le fichier généré doit être complet et directement exécutable avec docker compose
- ne fournir aucune explication
- retourner uniquement du YAML valide
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return clean_generated_content(response.text)

# =========================================================
# 3. GENERATION .GITLAB-CI.YML
# =========================================================

def generate_gitlab_ci(
    language,
    framework,
    docker_image_name,
    deployment_name,
    container_name
):
    prompt = f"""
Tu es un ingénieur DevOps expert en GitLab CI/CD, Docker,
Kubernetes et AWS EKS.

Génère un fichier .gitlab-ci.yml pour le projet suivant :

Langage : {language}
Framework : {framework}
Image Docker : {docker_image_name}
Deployment Kubernetes : {deployment_name}
Nom du conteneur Kubernetes : {container_name}

La pipeline doit contenir exactement trois stages :

1. test
2. build
3. deploy

TEST :
- utiliser une image Python adaptée si le langage est Python
- installer les dépendances depuis requirements.txt
- vérifier au minimum la syntaxe de l'application avec compileall
- pour Python, utiliser python:3.13-slim
- exécuter python -m compileall app.py models.py

BUILD :
- utiliser Docker
- construire l'image à partir du Dockerfile
- utiliser le GitLab Container Registry
- s'authentifier avec :
  CI_REGISTRY
  CI_REGISTRY_USER
  CI_REGISTRY_PASSWORD
- taguer l'image avec :
  $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
- pousser l'image vers GitLab Container Registry
- utiliser docker:29-cli
- utiliser docker:29-dind comme service
- utiliser echo "$CI_REGISTRY_PASSWORD" | docker login
  -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"

DEPLOY :
- déployer sur AWS EKS
- utiliser l'image registry.gitlab.com/gitlab-org/cloud-deploy/aws-base:latest

- utiliser une authentification GitLab OIDC vers AWS
- déclarer obligatoirement dans le job deploy un bloc GitLab id_tokens
- créer un token nommé GITLAB_OIDC_TOKEN avec :
  aud: sts.amazonaws.com

- utiliser la variable $AWS_ROLE_ARN pour le rôle IAM
- utiliser la variable $AWS_REGION pour la région AWS
- utiliser la variable $EKS_CLUSTER_NAME pour le cluster EKS

- récupérer des credentials AWS temporaires avec exactement :
  aws sts assume-role-with-web-identity
  --role-arn "$AWS_ROLE_ARN"
  --role-session-name "GitLabRunner-${{CI_PROJECT_ID}}-${{CI_PIPELINE_ID}}"
  --web-identity-token "$GITLAB_OIDC_TOKEN"
  --duration-seconds 3600
  --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
  --output text

- exporter les trois credentials temporaires retournés dans :
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_SESSION_TOKEN

- ne pas créer de fichier temporaire pour le token OIDC
- ne pas utiliser jq
- ne pas utiliser CI_OPENID_CONNECT_ID_TOKEN
- ne pas installer awscli avec pip

- installer ou rendre disponible kubectl
- exécuter aws eks update-kubeconfig avec :
  $AWS_REGION
  $EKS_CLUSTER_NAME

- mettre à jour l'image du Deployment Kubernetes :
  {deployment_name}

- mettre à jour le conteneur Kubernetes :
  {container_name}

- utiliser comme nouvelle image :
  $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

- attendre la fin du déploiement avec :
  kubectl rollout status deployment/{deployment_name} --timeout=300s

- exécuter le déploiement uniquement sur la branche main

Contraintes de sécurité :
- ne jamais écrire d'AWS Access Key ou Secret Key en dur
- ne jamais écrire de mot de passe ou token en dur
- utiliser les variables GitLab CI/CD
- utiliser GitLab OIDC pour l'authentification AWS
- ne fournir aucune explication
- retourner uniquement du YAML GitLab CI/CD valide
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return clean_generated_content(response.text)

   


# =========================================================
# 4. ANALYSE DES ERREURS DE DEPLOIEMENT
# =========================================================

def analyze_deployment_error(error_message):

    prompt = f"""
Tu es un assistant DevOps expert en :

- Linux
- Docker
- Docker Compose
- GitLab CI/CD
- GitLab Runner
- GitLab Container Registry
- Kubernetes
- AWS
- AWS IAM
- AWS EKS
- GitLab OIDC avec AWS
- PostgreSQL
- Prometheus
- Grafana

Contexte du projet :

- l'application est conteneurisée avec Docker
- la CI/CD utilise GitLab CI/CD
- les images Docker sont stockées dans GitLab Container Registry
- l'application est déployée sur Kubernetes avec AWS EKS
- l'authentification entre GitLab et AWS utilise OIDC
- Prometheus et Grafana sont utilisés pour le monitoring

Analyse l'erreur DevOps suivante :

--------------------
{error_message}
--------------------

Réponds en français.

La réponse doit obligatoirement contenir les sections suivantes :

1. Cause probable
- identifier les causes les plus plausibles
- ne jamais affirmer une cause sans preuve

2. Explication technique simple
- expliquer clairement ce que signifie l'erreur
- expliquer à quelle étape du workflow DevOps le problème peut se situer

3. Commandes de diagnostic
- proposer d'abord les commandes permettant de confirmer la cause
- privilégier les commandes adaptées à Linux, Docker, GitLab CI/CD,
  Kubernetes et AWS EKS selon le type d'erreur
- expliquer brièvement ce qu'il faut observer dans les résultats

4. Solution proposée
- proposer les corrections en fonction des résultats du diagnostic
- ne pas appliquer automatiquement une correction non confirmée

5. Vérification après correction
- fournir les commandes ou contrôles permettant de vérifier
  que le problème est réellement résolu

Règles importantes :

- ne suppose pas qu'une commande a réussi si l'information
  n'est pas disponible
- ne jamais inventer la cause exacte d'une erreur
- distinguer clairement une hypothèse d'une cause confirmée
- ne proposer Minikube que si l'erreur indique explicitement
  qu'il s'agit d'un environnement Minikube
- privilégier AWS EKS pour les problèmes Kubernetes de ce projet
- ne jamais demander d'afficher ou de copier un mot de passe,
  token, clé AWS, clé privée ou autre secret
- ne jamais proposer de mettre des secrets directement dans
  le code ou dans un fichier versionné
- utiliser les variables d'environnement ou les mécanismes
  sécurisés appropriés lorsqu'un secret est nécessaire
- fournir des commandes sûres et directement exploitables
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text.strip()

# =========================================================
# SAUVEGARDE AUTOMATIQUE
# =========================================================

def save_file(filename, content):

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"\n✅ Fichier généré : {filename}")


# =========================================================
# MENU PRINCIPAL
# =========================================================

def main():

    while True:

        print("\n" + "=" * 60)
        print("        ASSISTANT DEVOPS INTELLIGENT - LLM")
        print("=" * 60)

        print("\n1 - Générer un Dockerfile")
        print("2 - Générer docker-compose.yml")
        print("3 - Générer .gitlab-ci.yml")
        print("4 - Analyser une erreur de déploiement")
        print("0 - Quitter")

        choice = input("\nChoisissez une option : ").strip()

        # -------------------------------------------------
        # Dockerfile
        # -------------------------------------------------

        if choice == "1":

            language = input("Langage [Python] : ").strip() or "Python"

            framework = input("Framework [Flask] : ").strip() or "Flask"

            port = input("Port [5000] : ").strip() or "5000"

            requirements = (
                input("Fichier dépendances [requirements.txt] : ").strip()
                or "requirements.txt"
            )

            result = generate_dockerfile(
                language,
                framework,
                port,
                requirements
            )

            print("\n----- Dockerfile généré -----\n")
            print(result)

            save = input(
                "\nSauvegarder dans Dockerfile.generated ? (o/n) : "
            ).lower()

            if save == "o":
                save_file(
                    "Dockerfile.generated",
                    result
                )

        # -------------------------------------------------
        # Docker Compose
        # -------------------------------------------------

        elif choice == "2":

            app_name = (
                input(
                    "Nom application "
                    "[devops-dashboard] : "
                ).strip()
                or "devops-dashboard"
            )

            host_port = (
                input("Port hôte [5000] : ").strip()
                or "5000"
            )

            container_port = (
                input("Port conteneur [5000] : ").strip()
                or "5000"
            )

            result = generate_docker_compose(
                app_name,
                host_port,
                container_port
            )

            print("\n----- docker-compose.yml généré -----\n")
            print(result)

            save = input(
                "\nSauvegarder dans docker-compose.generated.yml ? (o/n) : "
            ).lower()

            if save == "o":
                save_file(
                    "docker-compose.generated.yml",
                    result
                )

        # -------------------------------------------------
        # GitLab CI/CD
        # -------------------------------------------------

        elif choice == "3":

            language = (
                input("Langage [Python] : ").strip()
                or "Python"
            )

            framework = (
                input("Framework [Flask] : ").strip()
                or "Flask"
            )

            image_name = (
                input(
                    "Image Docker "
                    "[dashboard-test] : "
                ).strip()
                or "dashboard-test"
            )

            deployment = (
                input(
                    "Deployment Kubernetes "
                    "[dashboard-deployment] : "
                ).strip()
                or "dashboard-deployment"
            )

            container = (
                input(
                    "Container Kubernetes "
                    "[dashboard-container] : "
                ).strip()
                or "dashboard-container"
            )

            result = generate_gitlab_ci(
                language,
                framework,
                image_name,
                deployment,
                container
            )

            print("\n----- .gitlab-ci.yml généré -----\n")
            print(result)

            save = input(
                "\nSauvegarder dans gitlab-ci.generated.yml ? (o/n) : "
            ).lower()

            if save == "o":
                save_file(
                    "gitlab-ci.generated.yml",
                    result
                )

        # -------------------------------------------------
        # Analyse erreur
        # -------------------------------------------------

        elif choice == "4":

            print(
                "\nCollez l'erreur de déploiement."
            )

            print(
                "Terminez par une ligne contenant seulement FIN.\n"
            )

            lines = []

            while True:

                line = input()

                if line.strip() == "FIN":
                    break

                lines.append(line)

            error_message = "\n".join(lines)

            if not error_message.strip():

                print("❌ Aucune erreur fournie.")
                continue

            result = analyze_deployment_error(
                error_message
            )

            print("\n----- Analyse LLM -----\n")
            print(result)

        # -------------------------------------------------
        # Quitter
        # -------------------------------------------------

        elif choice == "0":

            print("\nAssistant DevOps arrêté.")
            break

        else:

            print(
                "\n❌ Option invalide. "
                "Choisissez entre 0 et 4."
            )


# =========================================================
# EXECUTION
# =========================================================

if __name__ == "__main__":
    main()
