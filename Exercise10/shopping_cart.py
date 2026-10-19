from threading import Lock

from flask import Flask, jsonify, request


app = Flask(__name__)
cart = []
cart_lock = Lock()


@app.get("/cart")
def get_cart():
    with cart_lock:
        return jsonify(cart)


@app.post("/cart")
def add_to_cart():
    item = request.get_json(silent=True)
    if not isinstance(item, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Item must include a non-empty string 'name'."}), 400

    if "quantity" in item:
        quantity = item["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            return jsonify({"error": "'quantity' must be a positive integer."}), 400

    with cart_lock:
        cart.append(item)
        updated_cart = list(cart)
    return jsonify(updated_cart), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
