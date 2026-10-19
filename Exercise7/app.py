"""Small standard-library demo application for the Exercise 7 CI pipeline."""

import json


def application_status() -> dict[str, str]:
    """Return a simple status payload for the demo application."""
    return {
        "application": "Exercise 7 demo",
        "status": "ok",
        "message": "Python CI pipeline is ready.",
    }


def main() -> None:
    print(json.dumps(application_status(), indent=2))


if __name__ == "__main__":
    main()
