"""Simulate delivery operations and expose Prometheus metrics."""

from __future__ import annotations

import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Protocol, TypedDict
from urllib.parse import parse_qs, urlparse

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest


class DeliveryMetrics(TypedDict):
    total: int
    pending: int
    on_the_way: int
    average_time_minutes: float


class RandomSource(Protocol):
    def randint(self, a: int, b: int) -> int: ...

    def uniform(self, a: float, b: float) -> float: ...


SCENARIOS = {"normal", "high_pending", "long_delivery"}
registry = CollectorRegistry()
total_deliveries = Gauge(
    "deliveries_total", "Total number of simulated deliveries", registry=registry
)
pending_deliveries = Gauge(
    "deliveries_pending", "Number of deliveries waiting to be assigned", registry=registry
)
deliveries_on_the_way = Gauge(
    "deliveries_on_the_way", "Number of deliveries currently on the way", registry=registry
)
average_delivery_time = Gauge(
    "delivery_average_time_minutes",
    "Average delivery time in minutes",
    registry=registry,
)

state_lock = threading.Lock()
current_scenario = "normal"
current_total = 100


def sample_metrics(
    scenario: str, total: int, rng: RandomSource = random
) -> DeliveryMetrics:
    """Generate one deterministic-shape sample for the selected test scenario."""
    if scenario == "high_pending":
        pending = rng.randint(60, 80)
        average_time = rng.uniform(20, 35)
    elif scenario == "long_delivery":
        pending = rng.randint(5, 15)
        average_time = rng.uniform(60, 90)
    else:
        pending = rng.randint(5, 15)
        average_time = rng.uniform(15, 35)

    return {
        "total": total,
        "pending": pending,
        "on_the_way": rng.randint(6, 20),
        "average_time_minutes": round(average_time, 2),
    }


def update_metrics() -> DeliveryMetrics:
    global current_total
    with state_lock:
        current_total += random.randint(1, 3)
        sample = sample_metrics(current_scenario, current_total)
    total_deliveries.set(sample["total"])
    pending_deliveries.set(sample["pending"])
    deliveries_on_the_way.set(sample["on_the_way"])
    average_delivery_time.set(sample["average_time_minutes"])
    return sample


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global current_scenario
        request = urlparse(self.path)

        if request.path == "/metrics":
            body = generate_latest(registry)
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(body)
            return

        if request.path == "/control":
            scenario = parse_qs(request.query).get("scenario", [""])[0]
            if scenario not in SCENARIOS:
                self.send_error(
                    400,
                    "Use /control?scenario=normal, high_pending, or long_delivery",
                )
                return
            with state_lock:
                current_scenario = scenario
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Scenario set to {scenario}\n".encode())
            return

        self.send_error(404, "Use /metrics or /control?scenario=<name>")

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    port = int(os.environ.get("METRICS_PORT", "8000"))
    interval = float(os.environ.get("UPDATE_INTERVAL_SECONDS", "5"))
    if interval <= 0:
        raise ValueError("UPDATE_INTERVAL_SECONDS must be greater than zero")

    host = os.environ.get("METRICS_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Delivery metrics server listening on http://localhost:{port}/metrics")
    print(f"Control scenarios at http://localhost:{port}/control?scenario=<name>")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            sample = update_metrics()
            print(
                "Delivery metrics | "
                f"total: {sample['total']} | "
                f"pending: {sample['pending']} | "
                f"on the way: {sample['on_the_way']} | "
                f"average time: {sample['average_time_minutes']:.2f} min",
                flush=True,
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping delivery metrics application.")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
