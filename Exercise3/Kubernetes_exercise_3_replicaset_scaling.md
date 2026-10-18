# Kubernetes Exercise 3: ReplicaSet Scaling for a Flash Sale

## Objective
This exercise demonstrates how a ReplicaSet keeps multiple identical Flask Pods running in Kubernetes, how to scale them up from 3 to 5 replicas, and how Kubernetes self-heals by creating a replacement Pod when one is deleted. The scenario simulates a flash sale where traffic suddenly spikes and the application needs additional capacity.

## Real-world scenario
An online store experiences a sudden surge of visitors during a flash sale. Multiple identical app Pods help serve the load and improve resilience. The goal is not to prove a specific request rate or traffic pattern, but to show how Kubernetes keeps a predictable number of identical replicas available.

## Tools and prerequisites
- Windows 11
- VS Code
- Docker Desktop with Linux containers and WSL2
- Minikube with Docker driver
- kubectl
- Python and Flask
- Git and GitHub repository

Required software and versions should already be available in your local environment. Use PowerShell commands only.

## Architecture and traffic flow
- A Flask app exposes endpoints on port 5000.
- A ReplicaSet ensures 3 Pods start initially and maintains the target count.
- A ClusterIP Service routes traffic to the matching Pods.
- Each Pod has a `/health` endpoint used by readiness and liveness probes.
- The application runs inside a container built locally and loaded into Minikube with `imagePullPolicy: Never`.

Traffic flow:

1. Client request enters the Service.
2. The Service forwards traffic to a matching Pod with label `app: flashsale`.
3. The Pod responds with JSON data from the Flask app.
4. Kubernetes monitors pod health and maintains the desired replica count.

## What each file does
### `app.py`
This file creates the Flask API.
- `GET /` returns a welcome message, pod hostname, and current timestamp.
- `GET /buy` chooses a random product and accepts an optional `user` query parameter.
- `GET /health` returns a healthy response and pod hostname.
- The app binds to `0.0.0.0:5000`.

### `requirements.txt`
This installs the Python dependencies needed to run the Flask app with Gunicorn.

### `Dockerfile`
This builds a lightweight Python image, installs dependencies, exposes port 5000, and uses Gunicorn to start the Flask app.

### `flashsale-replicaset.yaml`
This file defines:
- `ReplicaSet` named `flashsale-rs`
- Initial replica count of 3
- Pod template labels matching `app: flashsale`
- A Service named `flashsale-svc` with type `ClusterIP`
- Readiness and liveness probes against `/health`
- Resource requests and limits for CPU and memory

### `screenshots/`
This folder is kept empty until you capture the actual terminal or browser screenshots after running the exercise.

## ReplicaSet, Pods, labels, selectors, probes, and resources
### ReplicaSet
A ReplicaSet ensures that a desired number of Pod replicas are running at all times. If a Pod disappears, Kubernetes creates a replacement until the desired count is reached again.

### Pods
A Pod is the smallest deployable unit in Kubernetes. Each pod runs one container in this exercise.

### Labels and selectors
Labels are key-value metadata used to identify Pods. The ReplicaSet selector matches `app: flashsale` and the Pod template uses the same label. This allows the ReplicaSet to manage only the matching Pods.

### Readiness and liveness probes
- Readiness probe: tells Kubernetes when the app is ready to receive traffic.
- Liveness probe: tells Kubernetes whether the app is still alive. If it fails, Kubernetes restarts the container.

### Resource requests and limits
- Requests: minimum resources the cluster should reserve for the Pod.
- Limits: maximum resources the container is allowed to use.

This exercise uses:
- CPU request: `100m`
- CPU limit: `500m`
- Memory request: `128Mi`
- Memory limit: `256Mi`

### ClusterIP Service
The Service named `flashsale-svc` exposes the app internally within the cluster. It selects Pods with `app: flashsale` and routes traffic to port 5000 on the target Pods.

## Implementation steps
Use these commands in Windows PowerShell.

### Stage A: Inspect and check prerequisites
```powershell
Set-Location 'C:\Users\LENOVO\Desktop\Devops\Exercise3'

docker info

& "C:\Program Files\Kubernetes\Minikube\minikube.exe" status

# Start Minikube only if it is not running
& "C:\Program Files\Kubernetes\Minikube\minikube.exe" start --driver=docker

kubectl get nodes
```

Check that the node reports `Ready` before continuing.

### Stage B: Build the image
```powershell
Set-Location 'C:\Users\LENOVO\Desktop\Devops\Exercise3'

docker build -t flashsale:1.0 .
docker images flashsale

& "C:\Program Files\Kubernetes\Minikube\minikube.exe" image load flashsale:1.0
```

The Dockerfile installs the dependencies with `RUN pip install --no-cache-dir -r requirements.txt`. Confirm the build succeeds and `docker images flashsale` lists `flashsale:1.0` before continuing. If Docker reports an error, stop and diagnose it before moving to deployment.

Validate the manifest before applying it:

```powershell
kubectl apply --dry-run=client -f .\flashsale-replicaset.yaml
```

### Stage C: Deploy the ReplicaSet
```powershell
Set-Location 'C:\Users\LENOVO\Desktop\Devops\Exercise3'

kubectl apply -f flashsale-replicaset.yaml
kubectl get rs
kubectl get pods -l app=flashsale
kubectl get services
```

Wait until all 3 Pods show `1/1 Running` and are ready.

### Stage D: Scale to five replicas
```powershell
kubectl scale rs flashsale-rs --replicas=5
kubectl get rs
kubectl get pods -l app=flashsale
```

Interpretation:
- `DESIRED`: the number of replicas the ReplicaSet should maintain.
- `CURRENT`: how many replicas currently exist.
- `READY`: how many are ready to receive traffic.
- `AVAILABLE`: how many are currently available to serve requests.

### Stage E: Demonstrate self-healing
```powershell
kubectl get pods -l app=flashsale

# Select an actual Flash Sale Pod name from Kubernetes and delete only that Pod
$podToDelete = kubectl get pods -l app=flashsale -o jsonpath='{.items[0].metadata.name}'
kubectl delete pod $podToDelete
kubectl get pods -l app=flashsale
```

When a Pod is deleted, the ReplicaSet creates a replacement. The replacement has a new Pod name. The deleted Pod does not restart under the same name. If deleting the Pod interrupts an active `kubectl port-forward service/flashsale-svc 8080:80` session, restart port-forwarding; it may have been connected to the Pod that was deleted.

### Stage F: Test the Service and Pod identities
Open a dedicated terminal and keep it running:

```powershell
kubectl port-forward service/flashsale-svc 8080:80
```

In a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/
Invoke-RestMethod "http://127.0.0.1:8080/buy?user=123"
Invoke-RestMethod http://127.0.0.1:8080/health
```

Inspect the `pod` value in the response. Requests can land on different Pods, but a different Pod hostname on every request is not guaranteed.

### Stage G: Inspect and record results
```powershell
kubectl describe rs flashsale-rs
kubectl get pods -l app=flashsale -o wide
kubectl get endpoints flashsale-svc
```

If `kubectl get endpoints` is unavailable, use:

```powershell
kubectl get endpointslices
```

Capture actual screenshots of the following:
- Initial 3 Pods
- Scaled 5 Pods
- Replacement Pod after deletion
- Successful API response from the Service

Save the screenshots in `Exercise3/screenshots/`.

## Observed results
| Check | Actual value / result |
|------|------------------------|
| Minikube status | Control plane, host, kubelet, and API server reported `Running`; kubeconfig was configured |
| Node readiness | Node `minikube` reported `Ready` on Kubernetes `v1.37.0` |
| Image build | `flashsale:1.0` built successfully; Flask and Gunicorn installed |
| Manifest validation | `kubectl apply --dry-run=client` accepted the ReplicaSet and Service |
| Initial ReplicaSet size | 3 desired, 3 current, 3 ready |
| Scaled ReplicaSet size | 5 desired, 5 current, 5 ready |
| Service | `flashsale-svc`, `ClusterIP`, port `80` to Pod port `5000` |
| API checks | `/` returned `Welcome to Big Sale!`; `/buy?user=123` returned item `Laptop`, user `123`, and status `success`; `/health` returned `healthy`. All returned a serving Pod hostname. |
| Deleted Pod | `flashsale-rs-crdbh` |
| Replacement Pod | `flashsale-rs-grn9k`; the ReplicaSet returned to 5 ready Pods |
| Endpoint check | The Service endpoint list contained five Pod endpoints on port `5000` |
| Pod placement | The five Pods were on the single `minikube` node |

## Screenshots
The following browser screenshots were captured from actual responses served through the local port-forward:

- `screenshots/api-root-response.png` — actual `/` JSON response.
- `screenshots/api-buy-response.png` — actual `/buy?user=123` JSON response.
- `screenshots/api-health-response.png` — actual `/health` JSON response.

Terminal screenshots for the initial 3 Pods, scaled 5 Pods, and replacement event have not been captured. Capture those from the real PowerShell terminal and save them in `screenshots/`; do not treat the command examples or recorded results as screenshots.

## Ten interview questions and concise answers
1. What does a ReplicaSet do?

   It maintains a fixed number of identical Pods and recreates them if needed.

2. Why use a Service?

   It provides stable access to Pods and load balancing across matching Pods.

3. What is the difference between a Deployment and a ReplicaSet?

   A Deployment manages rollout and updates, while a ReplicaSet mainly maintains a target replica count.

4. Why do we use a readiness probe?

   To ensure traffic is only sent to Pods that are ready.

5. Why do we use a liveness probe?

   To restart unhealthy containers automatically.

6. What is `imagePullPolicy: Never` used for?

   It tells Kubernetes to use a local image already loaded into Minikube.

7. Why do we label Pods with `app: flashsale`?

   To match the Service selector and ReplicaSet selector.

8. What happens when a Pod is deleted?

   The ReplicaSet creates a replacement to restore the desired count.

9. Does scaling replicas guarantee equal traffic distribution?

   No. It keeps multiple Pods running, but it does not guarantee identical traffic sharing or specific performance under load.

10. Why is this not a full-form autoscaling solution?

   Autoscaling requires a HorizontalPodAutoscaler and metrics or load-based triggers, not just replica changes.

## Troubleshooting
- If `kubectl get pods` shows `CrashLoopBackOff`, inspect logs with `kubectl logs <pod-name>`.
- If `kubectl get pods` shows `ImagePullBackOff`, verify that the image was loaded into Minikube using the `minikube image load` command.
- If the Service does not route traffic, verify the selector and the pod labels.
- If the app is not reachable through port-forward, ensure the port-forward command remains running in a separate terminal.
- If the ReplicaSet does not reach the desired count, use `kubectl describe rs flashsale-rs` and `kubectl describe pod <pod-name>` to investigate.

## Learning outcomes
- Learned how to create a Flask API with health, root, and purchase endpoints.
- Learned how to package the app in Docker.
- Learned how to load a local image into Minikube.
- Learned how to define a ReplicaSet and a ClusterIP Service in YAML.
- Learned how to scale from 3 to 5 replicas.
- Learned how Kubernetes self-heals by replacing a deleted Pod.
- Learned how to inspect Pods, ReplicaSets, and endpoints using kubectl.

## Important note
This exercise demonstrates Pod replication on a single Minikube node. It does not create multi-node high availability. All Pods run on the same node in this beginner setup, which is expected for this exercise.

A ReplicaSet keeps the target number of Pods running, but it is not the same as autoscaling. Real autoscaling requires a HorizontalPodAutoscaler and appropriate metrics.

## GitHub workflow after verification
Only after the exercise is successfully validated, run:

```powershell
git status
git add Exercise3
git commit -m "Add Kubernetes Exercise 3 ReplicaSet scaling"
git remote -v
```

Confirm that the remote is:

```powershell
https://github.com/divya-2005-s/Devops-Lab.git
```

Only then, if the commit succeeds, run:

```powershell
git push -u origin main
```

Do not stage unrelated files or rewrite earlier commits.

## Conclusion
This exercise shows how Kubernetes uses a ReplicaSet to maintain a desired number of identical app Pods, how a Service routes traffic to them, and how the cluster self-heals after a Pod is deleted. The app remains simple and beginner-friendly, but it demonstrates the core mechanics behind scaling and resilience in Kubernetes.
