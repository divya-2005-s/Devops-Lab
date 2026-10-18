# Exercise 5: Docker Security with AppArmor and Python

## Objective

Build a small Flask application and, on a Linux Docker host with AppArmor enabled, apply a restrictive AppArmor profile to its container and investigate restricted operations.

## Project files

- `app.py` — Flask endpoint on `0.0.0.0:5000`.
- `requirements.txt` — pinned Flask and Werkzeug dependencies.
- `Dockerfile` — builds the `flask-apparmor` image.
- `my-apparmor-profile` — candidate profile for the Python 3.12 image.
- `apply_apparmor.py` — Docker SDK build/run script that checks for AppArmor before requesting a profile.
- `test_restricted_actions.py` — tests file reading and shell execution without mislabeling unverified failures.
- `Screenshots/` — destination for screenshots captured by the learner.

## Environment compatibility and observed status

The checked environment is Windows 11 with Docker Desktop's `desktop-linux` context. The engine reports Linux containers, but its security options were `name=seccomp,profile=builtin` and `name=cgroupns`; AppArmor was not listed. Inside the Docker Linux environment, `/sys/module/apparmor/parameters/enabled` reported `N`; `apparmor_parser` and `aa-status` were unavailable.

Therefore, this Docker Desktop environment cannot load or enforce this custom profile. No system profile was loaded, no container was run with the profile, and no AppArmor restriction tests were claimed as successful. Installing AppArmor utilities inside an application container would not enable host-kernel enforcement.

For genuine enforcement, use an Ubuntu Linux VM or another Linux Docker host with AppArmor enabled and the Docker daemon advertising AppArmor support. Do not switch Docker contexts, alter WSL distributions, or change the current Docker Desktop configuration as part of this exercise without approval.

## Dependencies

Flask 3.1.1 and Werkzeug 3.1.3 are pinned to compatible versions for the Python 3.12 slim base image. The Docker SDK is needed by the host-side scripts; install it in the Python environment used to run the scripts only if it is not already installed:

```powershell
python -c "import docker; print(docker.__version__)"
```

If that import fails:

```powershell
python -m pip install docker
```

## Build and verify the application image

From PowerShell:

```powershell
Set-Location 'C:\Users\LENOVO\Desktop\Devops\Exercise5'
docker build -t flask-apparmor .
docker image inspect flask-apparmor
```

The usual host port 5000 is already occupied by an existing `kubectl.exe` port-forward to Minikube. That process and the Kubernetes resources were left untouched. For the smoke test, the Exercise5 container's port 5000 was published on host port 5002 instead. The actual smoke-test commands were:

```powershell
docker run -d --name flask-apparmor-smoke -p 5002:5000 flask-apparmor
docker ps --filter "name=^/flask-apparmor-smoke$"
docker inspect flask-apparmor-smoke --format 'Status={{.State.Status}} Image={{.Image}} AppArmorProfile={{.AppArmorProfile}} SecurityOpt={{json .HostConfig.SecurityOpt}}'
docker logs --tail 20 flask-apparmor-smoke
```

Host port 5000 was already occupied by a `kubectl.exe` port-forward to Minikube, so the Exercise5 container's port 5000 was published on host port 5002 instead. This smoke test ran with Docker's normal configuration, without the custom AppArmor profile. In PowerShell, the endpoint was checked with:

```powershell
curl.exe --noproxy '*' --fail --silent --show-error http://127.0.0.1:5002/
```

The actual response was:

```text
Hello, this is a secure Flask application running inside a Docker container!
```

This verifies the API response only; it is not AppArmor evidence. The smoke-test container is currently running so the captured response can be revisited. After it is no longer needed, clean up only this Exercise5 container:

```powershell
docker stop flask-apparmor-smoke
docker rm flask-apparmor-smoke
```

## Applying the profile on a supported Linux Docker host

The profile is written for the `python:3.12-slim` image and its `/usr/local/bin/python3.12` interpreter path. AppArmor paths and abstractions vary across host distributions; validate and adjust this profile on the actual target host. The profile allows the Python app and required runtime libraries, denies reads of sensitive shadow files, denies writes under `/etc` and `/var`, denies execution from `/bin` and `/usr/bin`, and denies `cap_sys_admin`. AppArmor's network rules authorize socket families/protocols, not a particular TCP port; Flask listens on port 5000 and Docker publishes that port.

On an approved Linux Docker host, from the Exercise5 project directory, review and install the profile as a host administrator:

```bash
sudo install -m 0644 my-apparmor-profile /etc/apparmor.d/my-apparmor-profile
sudo apparmor_parser -r -W /etc/apparmor.d/my-apparmor-profile
sudo aa-status
```

Only after parser validation and a status check show the profile loaded, install the Docker SDK if required, then run:

```bash
python3 apply_apparmor.py
```

The script builds the image, requires Docker Engine to advertise AppArmor, requests the loaded profile when creating the container, prints the reported profile and security options, and leaves the container running while you verify it. Press Enter in the script terminal to stop that Exercise5 container. It does not automatically remove containers with conflicting names.

The custom profile has **not** been syntax-validated or loaded in the current Docker Desktop environment because the parser and host AppArmor support are unavailable.

## Restricted-action tests on the supported host

With the profile-protected container running in another terminal:

```bash
python3 test_restricted_actions.py
```

The script reports each command, exit code, and observed result. A missing shell or an ordinary permission error is not called an AppArmor denial. Check host kernel/audit logs for an AppArmor `DENIED` record before claiming enforcement. Reading `/etc/passwd` may be permitted by the profile; the profile instead denies access to shadow files, so that test's result must be observed rather than assumed.

## Actual verification record

| Check | Result |
|---|---|
| Docker Linux backend | Confirmed with `docker context show` and `docker info --format`: context `desktop-linux`, `OSType=linux` |
| Docker Engine AppArmor support | Not available; AppArmor absent from engine security options |
| AppArmor kernel module | Disabled in Docker Linux environment (`N` from `/sys/module/apparmor/parameters/enabled`) |
| `apparmor_parser` / `aa-status` | Unavailable in the Docker Linux environment |
| Profile syntax/load/enforcement | Not tested; unsupported on the checked host |
| Python source syntax | Passed `python -m py_compile` for all three Python files |
| Docker SDK | Installed because it was missing; version 7.2.0 |
| Image build | Passed with `docker build -t flask-apparmor .`; SDK build also passed; final image ID begins `sha256:12035c95df4d` |
| Endpoint smoke test | Passed at `http://127.0.0.1:5002/`; exact expected greeting returned from the Exercise5 container. The first request to port 5000 reached the existing Minikube port-forward, so that output was not counted as an Exercise5 result. |
| Restricted actions | Not run; cannot establish AppArmor enforcement on this host |

The Docker SDK runner built the image and correctly refused to start a profile-protected container because the engine did not advertise AppArmor. The endpoint smoke-test container was separately run with Docker's normal configuration, without requesting the custom profile. It is currently running as `flask-apparmor-smoke` on host port 5002. An initial request via host port 5000 returned a response from the existing Minikube port-forward and was not counted; the Exercise5 response was subsequently verified inside its container and through host port 5002. Neither that port-forward nor any other exercise container was changed.

Update this table only with output observed from the host where each check runs.

## Screenshots

These files currently exist in the `Screenshots` folder:

- `Screenshots/docker-build.png` — file exists, but the captured image appears blank and does not visibly document the successful build. It is not accepted as build evidence.
- `Screenshots/app-response.png` — genuine browser capture showing the expected greeting at `http://127.0.0.1:5002/`. This documents only the unconfined smoke test, not AppArmor.

No `apparmor-profile.png` or `restricted-actions.png` files exist. Do not create those on this unsupported Docker Desktop environment. On a supported Linux Docker host, capture them only after verifying that the profile is loaded, applied, and producing corroborated enforcement evidence.

## Exercise questions

1. **What is the purpose of AppArmor with Docker containers?**  
   AppArmor applies a mandatory-access-control policy that limits what a container process can access or do, in addition to other Docker isolation.

2. **How do AppArmor profiles help secure a container?**  
   They define allowed and denied file, capability, execution, and network operations for processes running under the profile.

3. **Why restrict access to `/etc/` and `/var/`?**  
   `/etc/` contains system configuration and potentially sensitive files; `/var/` commonly holds logs, caches, and mutable service data. Restricting unnecessary access reduces damage from a compromised process.

4. **What other capabilities or actions can AppArmor restrict?**  
   It can restrict file reads/writes, executable launches, capabilities such as `CAP_SYS_ADMIN`, mount operations, signals, and supported network protocols.

5. **How can you verify that a profile is applied and enforcing restrictions?**  
   Confirm the profile is loaded on the Linux host, inspect the container's reported profile and Docker security options, exercise explicitly restricted operations, and corroborate failures with AppArmor audit/kernel `DENIED` logs. A failed command alone is insufficient evidence.

## Screenshot checklist

- `Screenshots/docker-build.png` — exists but is blank/unreadable; recapture if build evidence is needed.
- `Screenshots/app-response.png` — captured; actual app response from the smoke test, without custom AppArmor.
- `Screenshots/apparmor-profile.png` — not present; only create on a supported Linux host after confirming the profile is loaded and applied.
- `Screenshots/restricted-actions.png` — not present; only create on a supported Linux host with verified outcomes and audit evidence.
