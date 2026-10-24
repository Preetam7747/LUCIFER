from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from routes.auth import get_db, login_required, role_required

leave_bp = Blueprint("leave", __name__, url_prefix="/leave")


@leave_bp.route("/", methods=["GET", "POST"])
@login_required
def leave_requests():
    db = get_db()
    try:
        if request.method == "POST":
            reason = request.form.get("reason", "").strip()
            destination = request.form.get("destination", "").strip()
            departure = request.form.get("departure_time", "").strip()
            return_time = request.form.get("return_time", "").strip()

            if not all((reason, destination, departure, return_time)):
                flash("Please fill in every field.", "danger")
            elif return_time <= departure:
                flash("Return time must be after departure time.", "danger")
            else:
                db.execute("""
                    INSERT INTO leave_requests
                    (student_id, reason, destination, departure_time, return_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (session["user_id"], reason, destination, departure, return_time))
                db.commit()
                flash("Leave request submitted.", "success")
                return redirect(url_for("leave.leave_requests"))

        rows = db.execute(
            "SELECT * FROM leave_requests WHERE student_id=? ORDER BY created_at DESC",
            (session["user_id"],)
        ).fetchall()
        return render_template("student/leave.html", leave_requests=rows)
    finally:
        db.close()


@leave_bp.route("/<int:leave_id>/decision", methods=["POST"])
@role_required("admin")
def decision(leave_id):
    status = request.form.get("status", "")
    if status not in ("approved", "rejected"):
        flash("Invalid decision.", "danger")
        return redirect(url_for("admin.leave_requests"))

    db = get_db()
    try:
        db.execute(
            "UPDATE leave_requests SET status=? WHERE id=? AND status='pending'",
            (status, leave_id)
        )
        db.commit()
        flash("Leave request updated.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.leave_requests"))