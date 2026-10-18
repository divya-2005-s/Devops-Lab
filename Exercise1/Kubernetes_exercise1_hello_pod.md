# Exercise 1: Kubernetes Hello Pod

## Objective
To create and run an Nginx Pod in Kubernetes using Minikube and expose it through a NodePort Service.

## Tools Used
- Docker Desktop
- Minikube
- Kubernetes
- kubectl
- Nginx
- Visual Studio Code

## Steps Performed

### 1. Check Kubernetes Nodes
```powershell
kubectl get nodes
```
**Result:** The Minikube node was in the `Ready` state.

### 2. Create the Nginx Pod
```powershell
kubectl run hello-k8s --image=nginx --port=80
kubectl get pods
```
**Result:** The `hello-k8s` Pod reached `1/1 Running`.

### 3. Expose the Pod
```powershell
kubectl expose pod hello-k8s --type=NodePort --port=80
kubectl get services
```
**Result:** The Service was created with NodePort `31868`.

### 4. Verify the Service Endpoint
```powershell
kubectl get endpoints hello-k8s
```
**Result:** The endpoint was `10.244.0.3:80`.

### 5. Open the Nginx Service
```powershell
minikube service hello-k8s
```
This command opens the Nginx service in a browser when the service is reachable.

## Verification
- Kubernetes node: `minikube` — Ready
- Pod: `hello-k8s` — 1/1 Running
- Service type: NodePort
- Service port: 80
- NodePort: 31868
- Endpoint: `10.244.0.3:80`

## Screenshot
See `Nginx_Welcome_Page.png` for the browser screenshot, once captured.

## Learning Outcomes
- Learned how to create a Kubernetes Pod.
- Learned how to check Pod status.
- Learned how to expose a Pod through a NodePort Service.
- Learned how to verify Kubernetes services and endpoints.
