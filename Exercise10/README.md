# Kubernetes Multi-Node Exercise: Product Catalog and Shopping Cart

This exercise deploys two small Flask applications to a separate three-node Minikube profile. It does not use or alter the existing `minikube` profile.

## Important resource warning

At the last check (2026-10-19), the laptop had 8 GB RAM with only **0.61 GiB free**. Docker Desktop was running with a 4 GiB memory limit. **Do not build images or create/start the three-node cluster until there is adequate free memory.** As a practical target, first free at least 3–4 GiB on the Windows host and verify Docker Desktop has enough memory for the cluster; an 8 GB laptop may still struggle. If that headroom is not achievable, use a suitably sized remote Linux VM/cluster rather than weakening the three-node requirement. These files were prepared without building images, pulling images, starting a cluster, or applying manifests.

Before continuing, check memory and disk in PowerShell:

```powershell
Get-CimInstance Win32_OperatingSystem |
    Select-Object @{Name='FreeMemoryGiB';Expression={[math]::Round($_.FreePhysicalMemory / 1MB, 2)}},
                  @{Name='TotalMemoryGiB';Expression={[math]::Round($_.TotalVisibleMemorySize / 1MB, 2)}}
Get-PSDrive -Name C | Select-Object Name,Free
```

Close only applications you recognize and choose to close yourself. Do not stop unrelated containers or the existing `minikube` profile. If there is not enough free RAM for a 3-node cluster, defer the cluster stage rather than forcing resource-intensive work.

## Applications

- **Product Catalog**: `GET /products` returns Laptop (1200), Phone (800), and Headphones (150) as JSON.
- **Shopping Cart**: `GET /cart` returns the current cart. `POST /cart` accepts a JSON object with a non-empty `name` and optional positive-integer `quantity`; invalid JSON/items receive HTTP 400 and successful additions return HTTP 201.
- Shopping Cart storage is in memory only. It is not persistent across pod restarts, and separate replicas have separate carts. A Service request may reach a different replica, so do not treat the cart as shared or durable.

## Build the container images

Run from this directory in PowerShell after Docker Desktop is running and there is enough free memory:

```powershell
Set-Location 'C:\Users\LENOVO\Desktop\Devops\Kubernetes-MultiNode-Exercise'
docker build -f .\Dockerfile.product -t product-catalog:latest .
docker build -f .\Dockerfile.shopping -t shopping-cart:latest .
docker image inspect product-catalog:latest shopping-cart:latest
```

Both images use Python 3.12 slim and pinned Flask/runtime dependency versions. The build commands create only these named images; they do not remove other images.

## Create the isolated Minikube profile and load images

Check profile names before creating anything:

```powershell
minikube profile list
minikube -p devops-multinode status
```

If `devops-multinode` already exists, inspect its status/configuration and ask before changing it. If it does not exist and memory headroom is adequate, create a separate three-node Docker-driver profile:

```powershell
minikube start -p devops-multinode --driver=docker --nodes=3 --cpus=2
minikube -p devops-multinode node list
kubectl config use-context devops-multinode
kubectl config current-context
kubectl get nodes -o wide
```

Minikube's `--cpus` limits CPU allocated to Kubernetes; leave memory at the profile default unless you have checked the Docker driver's per-node resource behavior for your installed Minikube version. The start command may download Kubernetes and node images and uses substantial RAM and disk. Do not run it while memory is constrained. Confirm `kubectl config current-context` prints `devops-multinode` before using any command that does not specify `--context`. This does not stop or delete the existing `minikube` profile.

Load both local images through Minikube's profile-aware image loader (do not assume the Docker Desktop image store is automatically shared with every Minikube node):

```powershell
minikube -p devops-multinode image load product-catalog:latest
minikube -p devops-multinode image load shopping-cart:latest
```

Before deploying, verify that each image is present in the Minikube profile's node runtime. `imagePullPolicy: Never` in the Deployments is intentional: Kubernetes must find the images locally on the node where each pod is scheduled. If an image is unavailable on any eligible node, stop and resolve image distribution before applying a Deployment.

## Validate and apply manifests

These commands validate the YAML locally without applying it:

```powershell
python -c "import yaml, pathlib; files=['namespace.yaml','product_catalog_deployment.yaml','shopping_cart_deployment.yaml','product_catalog_service.yaml','shopping_cart_service.yaml']; [yaml.safe_load(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('All five YAML files parsed')"
kubectl --context devops-multinode apply --dry-run=client -f .\product_catalog_deployment.yaml
kubectl --context devops-multinode apply --dry-run=client -f .\shopping_cart_deployment.yaml
kubectl --context devops-multinode apply --dry-run=client -f .\product_catalog_service.yaml
kubectl --context devops-multinode apply --dry-run=client -f .\shopping_cart_service.yaml
kubectl --context devops-multinode apply --dry-run=client -f .\namespace.yaml
```

Apply the dedicated namespace first, then the application resources:

```powershell
kubectl --context devops-multinode apply -f .\namespace.yaml
```

Then apply the four application/service manifests:

```powershell
kubectl --context devops-multinode apply -f .\product_catalog_deployment.yaml
kubectl --context devops-multinode apply -f .\product_catalog_service.yaml
kubectl --context devops-multinode apply -f .\shopping_cart_deployment.yaml
kubectl --context devops-multinode apply -f .\shopping_cart_service.yaml
```

Both deployments use **preferred** pod anti-affinity (weight 100) keyed by `kubernetes.io/hostname`. Kubernetes will try to place replicas of the same application on different nodes but can still schedule them when that spread is not possible. This best-effort policy suits a small cluster and avoids leaving replicas Pending solely because of anti-affinity. Product Catalog's two replicas should normally spread across two nodes, and the three Shopping Cart replicas should normally spread across all three nodes. Five total replicas cannot each occupy a unique node in a three-node cluster; the policy spreads each application independently, so different applications may share a node. Verify actual placement with `kubectl get pods -A -o wide`.

## Verify scheduling and services

```powershell
kubectl --context devops-multinode get nodes -o wide
kubectl --context devops-multinode get deployments -A
kubectl --context devops-multinode get replicasets -A
kubectl --context devops-multinode get pods -A -o wide
kubectl --context devops-multinode get services -A
kubectl --context devops-multinode describe deployment product-catalog -n default
kubectl --context devops-multinode describe deployment shopping-cart -n devops-exercise
kubectl --context devops-multinode logs -n default -l app=product-catalog --all-containers=true --prefix=true --tail=100
kubectl --context devops-multinode logs -n devops-exercise -l app=shopping-cart --all-containers=true --prefix=true --tail=100
```

Expected: three Ready nodes, two available Product Catalog replicas in `default`, and three available Shopping Cart replicas in `devops-exercise`. The anti-affinity preference should spread each application's pods across different nodes when feasible; actual placement is confirmed only by `get pods -o wide`. For any pod not Ready, inspect `kubectl describe pod` and the events before retrying.

## Access and test

`kubectl port-forward` works from Windows PowerShell and does not require a terminal running `minikube service`:

```powershell
kubectl --context devops-multinode -n default port-forward service/product-catalog 18080:80
```

Leave that terminal open. In another PowerShell terminal:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:18080/products'
```

Stop port-forward with Ctrl+C. Start a separate forward for the cart:

```powershell
kubectl --context devops-multinode -n devops-exercise port-forward service/shopping-cart 18081:80
```

In another PowerShell terminal, check the cart and submit an item:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:18081/cart' -Method Get
$body = @{ name = 'Laptop'; quantity = 1 } | ConvertTo-Json
$response = Invoke-WebRequest -Uri 'http://127.0.0.1:18081/cart' -Method Post -ContentType 'application/json' -Body $body
$response.StatusCode
$response.Content | ConvertFrom-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:18081/cart' -Method Get
```

The POST should return HTTP 201 (PowerShell returns the response body on success). Because the cart is held in memory and the Service may direct requests to different replicas, successive requests are not guaranteed to see the same cart. For consistent single-pod testing, use a direct pod port-forward after listing the Shopping Cart pods:

```powershell
kubectl --context devops-multinode -n devops-exercise get pods -l app=shopping-cart -o wide
kubectl --context devops-multinode -n devops-exercise port-forward pod/<shopping-cart-pod-name> 18081:80
```

Replace `<shopping-cart-pod-name>` with one actual pod name. Keep the port-forward terminal open during the GET/POST/GET checks. This still does not make cart data persistent across restarts.

## Troubleshooting

- If `devops-multinode` is not listed, do not change the existing `minikube` profile. Check available RAM and create only the new profile using the command above.
- If a pod reports `ImagePullBackOff` or `ErrImageNeverPull`, verify the image was built and loaded into the `devops-multinode` profile on every node where it may run. The manifests use `imagePullPolicy: Never`.
- If a pod is Pending or not Ready, inspect `kubectl describe pod <pod-name> -n <namespace>` and `kubectl get events -A --sort-by=.lastTimestamp`. Do not blindly reapply or alter scheduling policy.
- If a port-forward cannot bind, choose another unused local port and update the corresponding URL.
- If a cart GET after POST does not show the item through the Service, use a direct pod port-forward as described above; replicas do not share in-memory state.

## Cleanup

These commands remove only the exercise's Kubernetes resources. Run them only after you have finished collecting evidence:

```powershell
kubectl --context devops-multinode delete -f .\product_catalog_deployment.yaml -f .\product_catalog_service.yaml
kubectl --context devops-multinode delete -f .\shopping_cart_deployment.yaml -f .\shopping_cart_service.yaml
kubectl --context devops-multinode delete -f .\namespace.yaml
minikube stop -p devops-multinode
```

The namespace deletion removes resources inside `devops-exercise`; inspect that namespace first if you added anything else there. Stopping the new profile preserves it for later. Do not run `minikube delete`, and do not stop or modify the existing `minikube` profile or unrelated containers.

## Screenshots

Capture only real output yourself with Windows + Shift + S and save it in `Screenshots/`:

1. `01-minikube-nodes.png` — all three nodes Ready.
2. `02-docker-images.png` — both application images.
3. `03-deployments-replicas.png` — requested/available deployment replicas (2 and 3).
4. `04-pods-node-distribution.png` — pod names, statuses, and node assignments.
5. `05-services.png` — both NodePort Services.
6. `06-product-catalog-response.png` — actual product JSON.
7. `07-shopping-cart-response.png` — actual GET and POST responses.
8. `08-github-exercise10-files.png` — Exercise10 files in the existing GitHub repository, after the changes are reviewed and pushed.

No screenshots are generated by the setup. Capture each only after the corresponding command or request succeeds.

## Validation status at file preparation

- Python syntax and local Flask test-client behavior: passed, including expected catalog JSON and cart success/error responses.
- YAML parsing and consistency of deployment selectors, service selectors, namespaces, replicas, ports, and preferred anti-affinity: passed using the preinstalled PyYAML parser.
- Static Dockerfile instruction checks: passed. `hadolint` is unavailable, and Docker image builds were not run.
- Minikube profile creation, image loading, manifest dry-runs against a live API, scheduling, and cluster HTTP access: not run. The laptop currently has only about 0.61 GiB free RAM, so resource-intensive steps are deferred.
- No cluster was started, no image was built or pulled, and no manifest was applied during file preparation.
