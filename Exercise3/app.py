import random
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)
PRODUCTS = ["Smartphone", "Shoes", "Headphones", "Laptop"]


@app.route("/")
def home():
    return jsonify(
        {
            "message": "Welcome to Big Sale!",
            "pod": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/buy")
def buy():
    item = random.choice(PRODUCTS)
    user = request.args.get("user", "guest")
    return jsonify(
        {
            "status": "success",
            "item": item,
            "user": user,
            "pod": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "pod": socket.gethostname()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
