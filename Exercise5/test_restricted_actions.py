import sys

import docker
from docker.errors import APIError, NotFound


CONTAINER_NAME = "flask-apparmor"


def describe_failure(output):
    lowered = output.lower()
    if "apparmor" in lowered and ("denied" in lowered or "audit" in lowered):
        return "AppArmor denial is indicated in command output; corroborate with host audit logs."
    if "not found" in lowered or "no such file" in lowered:
        return "The executable or file is missing; this does not prove AppArmor enforcement."
    if "permission denied" in lowered or "operation not permitted" in lowered:
        return "Permission failure; AppArmor attribution is unconfirmed without host audit logs."
    return "Failure reason is not attributable to AppArmor from this output alone."


def run_test(container, label, command):
    print(f"Command ({label}): {' '.join(command)}")
    try:
        result = container.exec_run(command, demux=True)
    except (APIError, NotFound) as error:
        message = str(error)
        print("Exit code: unavailable")
        print(f"Result: {describe_failure(message)}")
        print(f"Output: {message}")
        return

    stdout, stderr = result.output
    out_text = (stdout or b"").decode("utf-8", errors="replace").strip()
    err_text = (stderr or b"").decode("utf-8", errors="replace").strip()
    combined = "\n".join(part for part in (out_text, err_text) if part)
    print(f"Exit code: {result.exit_code}")
    print(
        "Result: "
        + ("Command completed." if result.exit_code == 0 else describe_failure(combined))
    )
    print(f"Output: {combined or '(no output)'}")


def main():
    client = docker.from_env()
    try:
        container = client.containers.get(CONTAINER_NAME)
        container.reload()
        if container.status != "running":
            raise RuntimeError(f"{CONTAINER_NAME} is {container.status}, not running.")

        security_options = client.info().get("SecurityOptions", [])
        profile = container.attrs.get("AppArmorProfile", "")
        if not any("apparmor" in item.lower() for item in security_options):
            raise RuntimeError(
                "Docker Engine does not advertise AppArmor support; refusing to "
                "describe command failures as AppArmor enforcement."
            )
        if not profile or profile.lower() == "unconfined":
            raise RuntimeError(
                f"Container AppArmor profile is not an active named profile: {profile!r}"
            )

        print(f"Container: {container.name} ({container.status})")
        print(f"Reported active AppArmor profile: {profile}")
        run_test(
            container,
            "read /etc/passwd",
            [
                "python",
                "-c",
                "from pathlib import Path; Path('/etc/passwd').read_text(); print('READ_OK')",
            ],
        )
        run_test(container, "execute /bin/bash", ["/bin/bash", "-c", "echo EXEC_OK"])
        print(
            "A nonzero exit code or permission error alone is not proof of AppArmor. "
            "Confirm denials in the Linux host's AppArmor audit/kernel logs."
        )
    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except (APIError, NotFound, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
