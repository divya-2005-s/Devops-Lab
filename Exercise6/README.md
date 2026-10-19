# Exercise 6: Real-Time Operations Monitoring and Alerting

This exercise simulates delivery operations, exports metrics from Python, scrapes them with Prometheus, visualizes them in Grafana, and defines threshold alerts.

## Objective and architecture

`delivery_metrics.py` updates simulated delivery measurements every five seconds. Prometheus scrapes the application and itself. Grafana is provisioned with Prometheus as its data source and a four-panel dashboard. A `/control` endpoint switches the simulator between normal, high-pending, and long-delivery scenarios for alert testing.

The Docker Compose network uses service DNS names (`delivery-metrics:8000` and `prometheus:9090`); host ports are bound to `127.0.0.1` only. The Grafana data volume is named `exercise6-grafana-data`.

## Prerequisites

- Windows 10/11, VS Code, PowerShell, and Python 3.10 or newer.
- Docker Desktop configured for Linux containers and running before Docker commands.
- At least 4 GB free disk space for the application, Prometheus, and Grafana images. Check with `Get-PSDrive -Name C`.
- Ports 8000, 9090, and 3000 available for the Compose stack. Jenkins commonly uses 8080. Check listeners before starting services; do not stop processes you do not recognize.

Docker Desktop's Linux engine was not running at the initial project setup, so no image build or container/Prometheus/Grafana checks have been claimed as successful. Start Docker Desktop yourself, then verify with `docker info` before proceeding with the container steps. If a Compose container name is already taken, inspect it before changing this exercise's container names; do not remove unrelated containers.

## Local Python setup

From a PowerShell terminal in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest -v
python .\delivery_metrics.py
```

The app prints changing delivery totals every five seconds. Stop it with Ctrl+C. If PowerShell blocks virtual-environment activation, use `.\.venv\Scripts\python.exe` instead of activating the environment.

Metrics are available at `http://localhost:8000/metrics`. The optional control endpoint accepts:

- `http://localhost:8000/control?scenario=normal`
- `http://localhost:8000/control?scenario=high_pending`
- `http://localhost:8000/control?scenario=long_delivery`

Use `Invoke-WebRequest -Uri http://localhost:8000/metrics` to inspect the actual response in PowerShell. Only use the control endpoint for this local exercise.

## Docker, Prometheus, and Grafana

Once Docker Desktop is running and the ports/container names are clear:

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

The app is at `http://localhost:8000/metrics`, Prometheus at `http://localhost:9090`, and Grafana at `http://localhost:3000`. Grafana's initial local exercise credentials are `admin` / `exercise6-admin`; change them if the service will be accessible beyond this machine.

In Prometheus, check **Status > Targets**: `delivery-app` and `prometheus` should be **UP**. Check `http://localhost:9090/-/ready` for readiness. Validate alert rules with:

```powershell
docker compose exec prometheus promtool check rules /etc/prometheus/alert_rules.yml
```

The Grafana **Delivery Operations** dashboard is provisioned automatically. It displays `deliveries_total`, `deliveries_pending`, `deliveries_on_the_way`, and `delivery_average_time_minutes`.

## Metrics and alerts

- `deliveries_total`: simulated total number of deliveries (increases over time).
- `deliveries_pending`: deliveries waiting for assignment.
- `deliveries_on_the_way`: deliveries currently on the way.
- `delivery_average_time_minutes`: simulated average delivery duration, in minutes.
- `HighPendingDeliveries`: pending count above 40 for one minute.
- `LongAverageDeliveryTime`: average time above 45 minutes for one minute.

For a controlled test, select a scenario using `/control?scenario=high_pending` or `/control?scenario=long_delivery`. In Prometheus **Alerts**, an alert first shows **Pending** while its `for: 1m` timer runs; it becomes **Firing** only after the condition remains true for the full minute. Return to `scenario=normal` after capturing the actual alert state.

Prometheus and Grafana are mapped to loopback only, but the demo Grafana password is intentionally simple. Do not expose this stack to an untrusted network.

## Jenkins

The Jenkinsfile runs dependency installation, Python bytecode compilation, and unit tests. Its Docker build stage is opt-in via the `BUILD_DOCKER_IMAGE` parameter (default `false`).

Run this pipeline on a Jenkins agent with Python and `sh` available. To enable the Docker stage, that agent must have a Docker CLI and explicitly authorized access to a Docker daemon. A Jenkins container does **not** automatically get host Docker access. Mounting the host Docker socket grants powerful host control; use only a deliberate, secured setup. This exercise does not install, recreate, or configure Jenkins.

Jenkins was not verified during initial setup. If Docker Desktop remains unavailable, leave the Docker stage disabled and run the Python checks on an agent with Python.

## Screenshot checkpoints

Capture screenshots yourself with Windows + Shift + S. Save them in `Screenshots/` using these exact names:

1. `01-python-metrics.png` — running Python terminal showing changing metrics.
2. `02-metrics-endpoint.png` — actual `/metrics` response.
3. `03-docker-containers.png` — running containers for this exercise.
4. `04-prometheus-targets.png` — Prometheus targets with the application **UP**.
5. `05-prometheus-alerts.png` — actual Prometheus alert state during controlled testing.
6. `06-grafana-dashboard.png` — the four-panel delivery dashboard.
7. `07-jenkins-pipeline.png` — successful Jenkins build, only if Jenkins is configured and run successfully.

Do not add a screenshot until you have captured the real output. The `Screenshots` directory starts empty.

## Starting and stopping only this exercise

Run these commands from this folder. They affect only the Compose project in this directory:

```powershell
docker compose up -d
docker compose down
```

`docker compose down` keeps the Grafana data volume. Do not add `--volumes` unless you intentionally want to erase this exercise's saved Grafana data. Never use a broad container cleanup command.

## Test results and limitations

At project creation, Python 3.13.5 was available, ports 8000/9090/3000/8080 were unoccupied, and 26.7 GB was free on C:. The isolated environment installed the pinned `prometheus-client` 0.23.1 successfully; Python compilation, all three unit tests, dependency consistency, and dashboard JSON parsing passed. Docker CLI 29.8.1 was present, but its Linux engine was unreachable. Application HTTP, image-build, Prometheus, Grafana, and Jenkins checks remain unverified until their corresponding commands are actually run. Screenshot files are not generated by this project setup.
