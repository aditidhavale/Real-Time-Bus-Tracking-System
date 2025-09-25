from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)

BUS_DATA_FILE = 'buses.json'

# Load buses from file or initialize
def load_buses():
    if not os.path.exists(BUS_DATA_FILE):
        with open(BUS_DATA_FILE, 'w') as f:
            json.dump({"buses": []}, f)
            return []

    try:
        with open(BUS_DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get("buses", [])
    except json.JSONDecodeError:
        with open(BUS_DATA_FILE, 'w') as f:
            json.dump({"buses": []}, f)
        return []


def save_buses(buses):
    with open(BUS_DATA_FILE, 'w') as f:
        json.dump({"buses": buses}, f, indent=2)

@app.route("/admin")
def admin_dashboard():
    return render_template("admin.html")

@app.route("/admin/get_buses")
def get_buses():
    buses = load_buses()
    return jsonify(buses)

@app.route("/admin/add_bus", methods=["POST"])
def add_bus():
    bus = request.json
    buses = load_buses()
    buses.append(bus)
    save_buses(buses)
    return jsonify({"success": True, "message": "Bus added!"})

if __name__ == "__main__":
    app.run(debug=True, port=5051)
