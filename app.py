from flask import Flask, send_from_directory, request, jsonify
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

FRONTEND_FOLDER = Path(__file__).resolve().parent / "frontend"

ALLOWED_PAGES = {
    "index.html",
    "login.html",
    "administrativepage.html",
    "complaints.html"
}

USERS = {
    "student": {"password": "student123", "role": "student"},
    "admin": {"password": "admin123", "role": "admin"},
    "staff": {"password": "staff123", "role": "staff"}
}

complaints = []


@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/<page>")
def serve_page(page):
    if page not in ALLOWED_PAGES:
        return "Page Not Found (404)", 404

    return send_from_directory(FRONTEND_FOLDER, page)


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    selected_role = data.get("role", "")

    user = USERS.get(username)

    if (
        user is None
        or user["password"] != password
        or user["role"] != selected_role
    ):
        return jsonify({
            "success": False,
            "message": "Invalid username, password, or role."
        }), 401

    destinations = {
        "student": "/complaints.html",
        "admin": "/administrativepage.html",
        "staff": "/complaints.html"
    }

    return jsonify({
        "success": True,
        "message": "Login successful!",
        "redirect": destinations[selected_role]
    })


@app.route("/api/complaints", methods=["GET", "POST"])
def manage_complaints():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}

        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        location = data.get("location", "").strip()
        image_url = data.get("image_url", "").strip()

        if not title or not description or not location:
            return jsonify({
                "success": False,
                "message": "Please provide a title, description, and location."
            }), 400

        complaint = {
            "id": len(complaints) + 1,
            "title": title,
            "description": description,
            "location": location,
            "image_url": image_url,
            "status": "Pending",
            "created_at": datetime.now().strftime("%d-%m-%Y %H:%M")
        }

        complaints.append(complaint)

        return jsonify({
            "success": True,
            "message": "Complaint submitted successfully.",
            "complaint": complaint
        }), 201

    return jsonify(complaints)


if __name__ == "__main__":
    app.run(debug=True)
