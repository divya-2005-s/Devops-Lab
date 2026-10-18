# Exercise 2: Deploy a Flask App on Minikube Using kubectl and YAML

## Objective
Deploy a Python Flask web application on a local Kubernetes cluster using Minikube, Docker, kubectl, and a YAML manifest.

## Tools Used
- Docker Desktop
- Minikube
- Kubernetes
- kubectl
- Python
- Flask
- Visual Studio Code

## Application Details
- Application: Flask
- Container image: `flask-app:latest`
- Container port: `15000`
- Deployment: `flask-app`
- Service: `flask-app-service`
- Service type: NodePort

## Implementation Steps

### 1. Create the Flask application
Created `app.py` to return the message:

`Hello from Flask on Kubernetes!`

The Flask application listens on `0.0.0.0:15000`.

### 2. Create the Docker image
Created a Dockerfile and `requirements.txt`, then built the image:

```powershell
docker build -t flask-app:latest .
```

The image was built successfully.

### 3. Load the image into Minikube

```powershell
minikube image load flask-app:latest
```

The local image was loaded for use by the Kubernetes cluster.

### 4. Deploy the application

```powershell
kubectl apply -f flask-deployment.yaml
```

The `flask-app` Deployment and `flask-app-service` Service were created successfully.

### 5. Verify the Deployment

```powershell
kubectl get nodes
kubectl get deployments
kubectl get pods -l app=flask-app
kubectl get services
```

Verified results:
- Minikube node: `Ready`
- Flask Pod: `1/1 Running`
- Deployment rollout: Successful
- Service type: `NodePort`
- Container port: `15000`
- Assigned NodePort: `32600`

### 6. Access the Flask application

```powershell
minikube service flask-app-service --url
```

This command provides a URL for accessing the application through the NodePort Service.

Expected browser response:

`Hello from Flask on Kubernetes!`

## Screenshot
Add `Flask_App_Output.png` after capturing the actual application response in the browser.

## Learning Outcomes
- Learned to containerize a Python Flask application with Docker.
- Learned to load a local image into Minikube.
- Learned to define a Deployment and Service using YAML.
- Learned to verify Pods, Deployments, and Services with kubectl.
- Learned how a NodePort Service exposes an application.

## Conclusion
The Flask application was successfully built into a Docker image and deployed to Minikube. The Deployment rollout completed successfully, and the Flask Pod reached the Running state. Browser verification should be completed and documented with a screenshot.
