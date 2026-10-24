import sqlite3

import sqlite3

from flask import (
    Blueprint, current_app, flash, redirect,
    render_template, request, session, url_for
)
from routes.auth import login_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_db():
    db_path = current_app.config.get("DATABASE_PATH")
    if not db_path:
        db_path = current_app.root_path + "/instance/hostel.db"

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@student_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    connection = get_db()

    try:
        user = connection.execute(
            "SELECT id, full_name, email, student_id, phone, role "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        complaints = connection.execute(
            "SELECT COUNT(*) FROM complaints WHERE student_id = ?",
            (user_id,),
        ).fetchone()[0]

        pending_leaves = connection.execute(
            "SELECT COUNT(*) FROM leave_requests "
            "WHERE student_id = ? AND status = 'pending'",
            (user_id,),
        ).fetchone()[0]

        payments = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments "
            "WHERE student_id = ? AND status = 'pending'",
            (user_id,),
        ).fetchone()[0]

        allocation = connection.execute(
            """
            SELECT r.room_number, r.block_name, r.monthly_fee
            FROM room_allocations ra
            JOIN rooms r ON r.id = ra.room_id
            WHERE ra.student_id = ? AND ra.status = 'active'
            ORDER BY ra.allocated_at DESC LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        notices = connection.execute(
            "SELECT title, content, created_at FROM notices "
            "ORDER BY created_at DESC LIMIT 5"
        ).fetchall()

        return render_template(
            "student/dashboard.html",
            user=user,
            complaints=complaints,
            pending_leaves=pending_leaves,
            pending_payments=payments,
            allocation=allocation,
            notices=notices,
        )
    finally:
        connection.close()


@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    connection = get_db()

    try:
        if request_method_is_post():
            from flask import request

            full_name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()

            if not full_name:
                flash("Full name is required.", "danger")
            else:
                connection.execute(
                    "UPDATE users SET full_name = ?, phone = ? WHERE id = ?",
                    (full_name, phone or None, user_id),
                )
                connection.commit()
                session["full_name"] = full_name
                flash("Profile updated successfully.", "success")
                return redirect(url_for("student.profile"))

        user = connection.execute(
            "SELECT id, full_name, email, student_id, phone "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        return render_template("student/profile.html", user=user)
    finally:
        connection.close()


def request_method_is_post():
    from flask import request
    return request.method == "POST"


@student_bp.route("/room")
@login_required
def room():
    connection = get_db()
    try:
        allocation = connection.execute(
            """
            SELECT r.*
            FROM room_allocations ra
            JOIN rooms r ON r.id = ra.room_id
            WHERE ra.student_id = ? AND ra.status = 'active'
            ORDER BY ra.allocated_at DESC LIMIT 1
            """,
            (session["user_id"],),
        ).fetchone()

        return render_template("student/room.html", allocation=allocation)
    finally:
        connection.close()


@student_bp.route("/complaints")
@login_required
def complaints():
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT * FROM complaints WHERE student_id = ? "
            "ORDER BY created_at DESC",
            (session["user_id"],),
        ).fetchall()
        return render_template("student/complaints.html", complaints=rows)
    finally:
        connection.close()


@student_bp.route("/leave")
@login_required
def leave():
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT * FROM leave_requests WHERE student_id = ? "
            "ORDER BY created_at DESC",
            (session["user_id"],),
        ).fetchall()
        return render_template("student/leave.html", leave_requests=rows)
    finally:
        connection.close()


@student_bp.route("/mess")
@login_required
def mess():
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT * FROM mess_menu ORDER BY meal_date, meal_type"
        ).fetchall()
        return render_template("student/mess.html", menu=rows)
    finally:
        connection.close()


@student_bp.route("/payments")
@login_required
def payments():
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT * FROM payments WHERE student_id = ? ORDER BY created_at DESC",
            (session["user_id"],),
        ).fetchall()
        return render_template("student/payments.html", payments=rows)
    finally:
        connection.close()


@student_bp.route("/notices")
@login_required
def notices():
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT * FROM notices ORDER BY created_at DESC"
        ).fetchall()
        return render_template("student/notices.html", notices=rows)
    finally:
        connection.close()