from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"

GOOGLE_MAPS_API_KEY = "AIzaSyBl-iQpn5pS8GKZdiTQ8RsplJ2KaZxeTtU"

# Load route (bus) data once
with open("route.json") as f:
    route_data = json.load(f)

@app.route("/")
def root_redirect():
    return redirect(url_for("splash"))

@app.route("/splash")
def splash():
    return render_template("splash.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Load fresh user data every time
    with open("users.json") as f:
        user_data = json.load(f)

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        for user in user_data["users"]:
            if user["username"] == username and user["password"] == password:
                session["username"] = username
                return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    buses = route_data["routes"]
    stations = sorted(set(station for route in buses for station in route["stations"]))
    return render_template("index.html", buses=buses, stations=stations, username=session["username"])

@app.route("/get_eta", methods=["POST"])
def get_eta():
    data = request.get_json()
    bus_id = data.get("bus_id")
    from_station = data.get("from_station")
    to_station = data.get("to_station")

    selected_bus = next((bus for bus in route_data["routes"] if bus["id"] == bus_id), None)
    if not selected_bus:
        return jsonify({"error": "Bus not found"}), 404

    if from_station not in selected_bus["stations"] or to_station not in selected_bus["stations"]:
        return jsonify({"error": "Invalid stations"}), 400

    origin = selected_bus["current_location"]
    destination_name = to_station + ", India"

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin['lat']},{origin['lng']}",
        "destinations": destination_name,
        "departure_time": "now",
        "traffic_model": "best_guess",
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params).json()

    try:
        eta_seconds = response["rows"][0]["elements"][0]["duration_in_traffic"]["value"]
        eta_minutes = eta_seconds // 60
        eta_text = response["rows"][0]["elements"][0]["duration_in_traffic"]["text"]
    except Exception:
        eta_minutes = 0
        eta_text = "Unavailable"

    try:
        dispatch_dt = datetime.strptime(selected_bus["dispatch_time"], "%I:%M %p")
        arrival_dt = dispatch_dt + timedelta(minutes=eta_minutes)
        arrival_time_str = arrival_dt.strftime("%I:%M %p")
    except Exception:
        arrival_time_str = "Unavailable"

    return jsonify({
        "eta_minutes": eta_text,
        "arrival_time": arrival_time_str,
        "dispatch_time": selected_bus["dispatch_time"],
        "driver_contact": selected_bus["driver_contact"],
        "bus_number": selected_bus["bus_number"],
        "current_location": origin
    })

if __name__ == "__main__":
    app.run(debug=True)
