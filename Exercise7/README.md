# Exercise 7: Continuous Integration (CI) and Jenkins

## Objective and architecture

This exercise uses a small standard-library Python program, an automated `unittest` test, and a Jenkins Declarative Pipeline. Jenkins runs source validation, checks Python and pip, compiles the Python files, and executes the test. It attempts a Docker image build only when the Jenkins agent can reach a Docker daemon; otherwise it logs that the optional stage is blocked without hiding failures in the Python stages.

The project files remain in `Exercise7`. For a local Jenkins run before any Git commit or push, the Jenkins container can read the repository through a read-only bind mount at `/workspace`; the Pipeline job uses `/workspace/Exercise7`. No Git changes or pushes are part of this exercise.

## Prerequisites

- Windows 10/11, VS Code, PowerShell, Python 3.10+, and Docker Desktop using Linux containers.
- About 4 GB free disk space for a Jenkins image and its build layers; check with `Get-PSDrive -Name C`.
- Ports 8080 (Jenkins web UI) and 50000 (inbound agents) available. Check before installation and do not stop an unidentified process.
- Docker Desktop must be running for Docker commands.

At initial inspection on 2026-10-19, Docker Desktop's Linux engine responded, Python 3.13.5 was available, both ports were free, and C: had about 26.84 GiB free. There were no Jenkins containers or Jenkins-named images. Three existing volumes were inspected and left untouched: two anonymous volumes and `minikube`. The repository worktree was clean and `Exercise7` did not exist.

## Run and test locally

Open a PowerShell terminal in this folder:

```powershell
python --version
python -m compileall -q app.py test_app.py
python -m unittest -v
python .\app.py
```

`requirements.txt` documents that the app uses only the Python standard library; no third-party dependency installation is needed. The demo prints a JSON status message.

Build and run the demo image when Docker is available:

```powershell
docker build -t exercise7-demo:local .
docker run --rm exercise7-demo:local
```

## Jenkins setup (new installation only)

The inspection found no Jenkins installation to reuse. Before starting a new container, re-check ports 8080 and 50000 and check that the name `exercise7-jenkins` and volume `exercise7-jenkins-home` have not since been taken. Never delete or recreate an existing Jenkins container or volume.

This project includes a small Jenkins image definition with Python and Git for the built-in Jenkins agent. From this directory, build the image:

```powershell
docker build -f .\jenkins\Dockerfile -t exercise7-jenkins:local .
```

Then start a **new** Jenkins container with a dedicated persistent volume. The repository mount is read-only; Jenkins data persists separately:

```powershell
docker run -d --name exercise7-jenkins --restart unless-stopped `
  -p 127.0.0.1:8080:8080 -p 127.0.0.1:50000:50000 `
  --mount source=exercise7-jenkins-home,target=/var/jenkins_home `
  --mount "type=bind,source=C:\Users\LENOVO\Desktop\Devops,target=/workspace,readonly" `
  exercise7-jenkins:local
```

This command does not grant Jenkins access to the Docker daemon. It uses loopback ports and a read-only source mount. Jenkins runs a service with elevated control over its stored credentials and jobs; keep the UI on this machine and protect the admin account.

Check the container with `docker ps --filter name=exercise7-jenkins`. Retrieve the initial password only in a private PowerShell terminal:

```powershell
docker exec exercise7-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Type it into `http://localhost:8080` to unlock Jenkins. Do not paste it into chat, save it in the project, or include it in a screenshot. Complete the recommended plugin installation and create an administrator account.

### Create the Pipeline job

1. In Jenkins, choose **New Item**, enter a job name such as `exercise7-ci`, select **Pipeline**, then choose **OK**.
2. Under **Pipeline**, choose **Pipeline script**. Copy the contents of this folder's `Jenkinsfile` into the script box, then save. This local method keeps the exercise uncommitted and unpushed; repeat the copy if you later change the file.
3. Build with the default `SOURCE_DIRECTORY` value `/workspace/Exercise7`. The read-only mount makes the local project source available to Jenkins. If configuring an SCM-backed job later, check out the source and set `SOURCE_DIRECTORY` to `.`.
4. Review **Console Output** and the stage view. The Docker stage may explicitly log `BLOCKED` when the Jenkins agent lacks Docker access; Python syntax and tests still run first.

For an SCM-backed Pipeline job, the source repository must be reachable by Jenkins and contain the Jenkinsfile. This project is initially untracked; do not expect Jenkins to retrieve uncommitted local files through SCM. Commit/push only after you explicitly decide to do so.

## Docker access from Jenkins

A Jenkins container does not automatically control the host Docker daemon. The provided Jenkins image intentionally does not include the Docker CLI or mount a daemon socket. The pipeline probes Docker access and reports the image stage as blocked if the CLI or daemon is unavailable; it does not silently claim an image was built.

Enabling Docker builds requires deliberately configuring both a Docker CLI and an authorized daemon endpoint for the Jenkins **build agent**. Mounting a Docker socket or granting a remote daemon can give Jenkins jobs powerful control over the host. Do not add such access casually; this project does not configure it.

## Pipeline stages

1. **Use project source** — verifies the expected source files are present.
2. **Python version and dependencies** — checks Python 3.10 or newer, pip availability, and the installed dependency set.
3. **Python syntax validation** — compiles the application and test file.
4. **Unit tests** — runs the Python `unittest` suite.
5. **Docker image build (optional)** — builds `exercise7-demo:ci` only if Docker is accessible; otherwise the console explicitly says the stage is blocked.

Failed Python checks or a failed image build fail the Jenkins build. Docker being inaccessible is reported as a blocked optional build and does not disguise Python test failures.

## Screenshot checkpoints

Capture real output with **Windows + Shift + S** and save it in `Screenshots/`. Do not capture passwords, tokens, or other secrets.

- `01-docker-status.png` — Docker status and relevant Jenkins container status.
- `02-jenkins-running.png` — the new Jenkins container running.
- `03-jenkins-dashboard.png` — Jenkins dashboard after initial setup.
- `04-pipeline-configuration.png` — Pipeline job configured with the project's `Jenkinsfile`.
- `05-pipeline-success.png` — actual successful build and stage results.
- `06-test-results.png` — actual Python test results if not visible in the successful pipeline output.

Only capture a checkpoint after the corresponding real output exists. Do not create placeholder screenshots.

## Test results and known limitations

Initial inspection confirmed Docker Desktop was running, Python 3.13.5 was available, ports 8080 and 50000 were free, and 26.84 GiB was free on C:. No Jenkins container/image was present. Locally, Python syntax compilation passed, the `unittest` suite passed (1 test), `pip check` reported no broken requirements, and `app.py` printed its expected JSON status. The application Docker image has not been built. Jenkinsfile execution/linting, Jenkins installation, pipeline execution, and screenshot capture have not yet been performed; no Groovy or Java executable and no Jenkins image were found during inspection.

The Docker build stage is intentionally conditional on the build agent's Docker access. The default Jenkins setup keeps that access disabled for safety. The local Pipeline script method requires copying `Jenkinsfile` into the Jenkins job; SCM checkout becomes available only after the Jenkins agent can access a repository version containing the file.
