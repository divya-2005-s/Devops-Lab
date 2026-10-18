from pathlib import Path
import sys

import docker
from docker.errors import APIError, NotFound


PROJECT_DIR = Path(__file__).resolve().parent
IMAGE_NAME = "flask-apparmor"
CONTAINER_NAME = "flask-apparmor"
PROFILE_NAME = "my-apparmor-profile"


def main():
    client = docker.from_env()
    client.ping()

    try:
        image, build_logs = client.images.build(
            path=str(PROJECT_DIR),
            tag=IMAGE_NAME,
            rm=True,
        )
    except (APIError, OSError) as error:
        raise RuntimeError(f"Image build failed: {error}") from error

    print(f"Built image {IMAGE_NAME}: {image.id}")
    for entry in build_logs:
        stream = entry.get("stream")
        if stream:
            print(stream, end="")

    security_options = client.info().get("SecurityOptions", [])
    if not any("apparmor" in option.lower() for option in security_options):
        raise RuntimeError(
            "Docker Engine does not advertise AppArmor support. "
            f"SecurityOptions={security_options!r}. "
            "No container was started; use a supported Linux Docker host."
        )

    try:
        existing = client.containers.get(CONTAINER_NAME)
    except NotFound:
        existing = None
    if existing is not None:
        raise RuntimeError(
            f"Container {CONTAINER_NAME!r} already exists. Inspect it before reuse "
            "or removal; this script will not replace it automatically."
        )

    container = None
    try:
        container = client.containers.run(
            image=IMAGE_NAME,
            name=CONTAINER_NAME,
            detach=True,
            ports={"5000/tcp": 5000},
            security_opt=[f"apparmor={PROFILE_NAME}"],
        )
        container.reload()
        print(f"Container state: {container.status}")
        print(f"Configured AppArmor profile: {container.attrs.get('AppArmorProfile')}")
        print(
            "Configured security options: "
            f"{container.attrs['HostConfig'].get('SecurityOpt')}"
        )
        print("Test http://localhost:5000/ from another terminal.")
        input("Press Enter after verification to stop this Exercise5 container: ")
    except KeyboardInterrupt:
        print("\nStop requested.")
    except APIError as error:
        raise RuntimeError(
            "Docker could not start the container with the requested profile. "
            "This is not proof that the profile was enforced; check that the "
            "profile was loaded on the Docker host and inspect the daemon error."
        ) from error
    finally:
        if container is not None:
            container.reload()
            if container.status == "running":
                container.stop(timeout=10)
                print(f"Stopped {CONTAINER_NAME}. The container was not removed.")
        client.close()


if __name__ == "__main__":
    try:
        main()
    except (APIError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
