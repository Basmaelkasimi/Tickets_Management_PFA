from flask import Flask, render_template, request
from assistant_ai.llm.llm_service import (
    generate_dockerfile,
    generate_docker_compose,
    generate_gitlab_ci,
    analyze_deployment_error,
)

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    selected_tool = "dockerfile"

    if request.method == "POST":
        selected_tool = request.form.get("tool")

        try:
            if selected_tool == "dockerfile":
                language = request.form.get("language", "Python")
                framework = request.form.get("framework", "Flask")
                port = request.form.get("port", "5000")
                requirements = request.form.get(
                    "requirements",
                    "requirements.txt"
                )

                result = generate_dockerfile(
                    language,
                    framework,
                    port,
                    requirements
                )

            elif selected_tool == "compose":
                app_name = request.form.get(
                    "app_name",
                    "devops-app"
                )
                host_port = request.form.get(
                    "host_port",
                    "5000"
                )
                container_port = request.form.get(
                    "container_port",
                    "5000"
                )

                result = generate_docker_compose(
                    app_name,
                    host_port,
                    container_port
                )

            elif selected_tool == "gitlab":
                language = request.form.get("language", "Python")
                framework = request.form.get("framework", "Flask")
                image_name = request.form.get(
                    "image_name",
                    "devops-app"
                )
                deployment = request.form.get(
                    "deployment",
                    "app-deployment"
                )
                container = request.form.get(
                    "container",
                    "app-container"
                )

                result = generate_gitlab_ci(
                    language,
                    framework,
                    image_name,
                    deployment,
                    container
                )

            elif selected_tool == "diagnostic":
                error_message = request.form.get(
                    "error_message",
                    ""
                )

                if error_message.strip():
                    result = analyze_deployment_error(
                        error_message
                    )
                else:
                    result = "Veuillez saisir une erreur à analyser."

        except Exception as error:
            result = f"Erreur : {error}"

    return render_template(
        "index.html",
        result=result,
        selected_tool=selected_tool,
    )


@app.route("/health")
def health():
    return {
        "status": "healthy",
        "service": "devops-ai-assistant",
        "version": "1.0.0",
    }, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5050,
        debug=False
    )