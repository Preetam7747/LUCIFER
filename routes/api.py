from flask import Blueprint, jsonify, session
from routes.auth import get_db, login_required, role_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "application": "Smart Hostel Management System"})


@api_bp.route("/student/summary")
@login_required
def student_summary():
    db = get_db()
    try:
        user_id = session["user_id"]

        complaints = db.execute(
            "SELECT COUNT(*) FROM complaints WHERE student_id=?",
            (user_id,)
        ).fetchone()[0]

        pending_leaves = db.execute(
            "SELECT COUNT(*) FROM leave_requests WHERE student_id=? AND status='pending'",
            (user_id,)
        ).fetchone()[0]

        pending_payments = db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments "
            "WHERE student_id=? AND status='pending'",
            (user_id,)
        ).fetchone()[0]

        return jsonify({
            "complaints": complaints,
            "pending_leaves": pending_leaves,
            "pending_payments": pending_payments
        })
    finally:
        db.close()


@api_bp.route("/admin/summary")
@role_required("admin")
def admin_summary():
    db = get_db()
    try:
        return jsonify({
            "students": db.execute(
                "SELECT COUNT(*) FROM users WHERE role='student'"
            ).fetchone()[0],
            "rooms": db.execute(
                "SELECT COUNT(*) FROM rooms"
            ).fetchone()[0],
            "complaints": db.execute(
                "SELECT COUNT(*) FROM complaints WHERE status='pending'"
            ).fetchone()[0],
            "leave_requests": db.execute(
                "SELECT COUNT(*) FROM leave_requests WHERE status='pending'"
            ).fetchone()[0]
        })
    finally:
        db.close()