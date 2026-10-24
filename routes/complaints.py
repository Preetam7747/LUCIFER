from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from routes.auth import get_db, login_required, role_required

complaints_bp = Blueprint("complaints", __name__, url_prefix="/complaints")


@complaints_bp.route("/")
@login_required
def list_complaints():
    db = get_db()
    try:
        if session.get("role") == "admin":
            rows = db.execute("""
                SELECT c.*, u.full_name FROM complaints c
                JOIN users u ON u.id=c.student_id ORDER BY c.created_at DESC
            """).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM complaints WHERE student_id=? ORDER BY created_at DESC",
                (session["user_id"],)
            ).fetchall()
        return render_template("student/complaints.html", complaints=rows)
    finally:
        db.close()


@complaints_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_complaint():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "other").strip()
        if not title or not description:
            flash("Enter a title and description.", "danger")
            return render_template("student/new_complaint.html")

        db = get_db()
        try:
            db.execute("""
                INSERT INTO complaints (student_id, title, description, category)
                VALUES (?, ?, ?, ?)
            """, (session["user_id"], title, description, category or "other"))
            db.commit()
            flash("Complaint submitted.", "success")
            return redirect(url_for("complaints.list_complaints"))
        finally:
            db.close()
    return render_template("student/new_complaint.html")


@complaints_bp.route("/<int:complaint_id>/status", methods=["POST"])
@role_required("admin", "staff")
def update_status(complaint_id):
    status = request.form.get("status", "")
    if status not in ("pending", "in_progress", "resolved", "rejected"):
        flash("Invalid complaint status.", "danger")
        return redirect(url_for("admin.complaints"))

    db = get_db()
    try:
        db.execute(
            "UPDATE complaints SET status=? WHERE id=?",
            (status, complaint_id)
        )
        db.commit()
        flash("Complaint status updated.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.complaints"))