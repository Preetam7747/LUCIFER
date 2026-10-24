import sqlite3
from flask import Blueprint, flash, redirect, render_template, request, url_for
from routes.auth import get_db, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    db = get_db()
    try:
        stats = {
            "students": db.execute(
                "SELECT COUNT(*) FROM users WHERE role='student'"
            ).fetchone()[0],
            "rooms": db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
            "complaints": db.execute(
                "SELECT COUNT(*) FROM complaints WHERE status='pending'"
            ).fetchone()[0],
            "leaves": db.execute(
                "SELECT COUNT(*) FROM leave_requests WHERE status='pending'"
            ).fetchone()[0],
        }
        return render_template("admin/dashboard.html", stats=stats)
    finally:
        db.close()


@admin_bp.route("/students")
@role_required("admin")
def students():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT id, full_name, email, student_id, phone, created_at "
            "FROM users WHERE role='student' ORDER BY full_name"
        ).fetchall()
        return render_template("admin/students.html", students=rows)
    finally:
        db.close()


@admin_bp.route("/rooms")
@role_required("admin")
def rooms():
    db = get_db()
    try:
        rows = db.execute("SELECT * FROM rooms ORDER BY room_number").fetchall()
        return render_template("admin/rooms.html", rooms=rows)
    finally:
        db.close()


@admin_bp.route("/allocations")
@role_required("admin")
def allocations():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT ra.id, ra.allocated_at, ra.status,
                   u.full_name, u.student_id, r.room_number, r.block_name
            FROM room_allocations ra
            JOIN users u ON u.id=ra.student_id
            JOIN rooms r ON r.id=ra.room_id
            ORDER BY ra.allocated_at DESC
        """).fetchall()
        return render_template("admin/allocations.html", allocations=rows)
    finally:
        db.close()


@admin_bp.route("/complaints")
@role_required("admin")
def complaints():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT c.*, u.full_name
            FROM complaints c JOIN users u ON u.id=c.student_id
            ORDER BY c.created_at DESC
        """).fetchall()
        return render_template("admin/complaints.html", complaints=rows)
    finally:
        db.close()


@admin_bp.route("/leave-requests")
@role_required("admin")
def leave_requests():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT l.*, u.full_name
            FROM leave_requests l JOIN users u ON u.id=l.student_id
            ORDER BY l.created_at DESC
        """).fetchall()
        return render_template("admin/leave_requests.html", leave_requests=rows)
    finally:
        db.close()


@admin_bp.route("/mess", methods=["GET", "POST"])
@role_required("admin")
def mess_management():
    db = get_db()
    try:
        if request.method == "POST":
            date = request.form.get("meal_date", "").strip()
            meal = request.form.get("meal_type", "").strip().lower()
            items = request.form.get("menu_items", "").strip()
            if date and meal in ("breakfast", "lunch", "snacks", "dinner") and items:
                db.execute("""
                    INSERT INTO mess_menu (meal_date, meal_type, menu_items)
                    VALUES (?, ?, ?)
                    ON CONFLICT(meal_date, meal_type)
                    DO UPDATE SET menu_items=excluded.menu_items
                """, (date, meal, items))
                db.commit()
                flash("Menu saved.", "success")
            else:
                flash("Enter a date, valid meal type, and menu items.", "danger")
            return redirect(url_for("admin.mess_management"))

        rows = db.execute(
            "SELECT * FROM mess_menu ORDER BY meal_date DESC, meal_type"
        ).fetchall()
        return render_template("admin/mess_management.html", menu=rows)
    finally:
        db.close()


@admin_bp.route("/payments")
@role_required("admin")
def payments():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT p.*, u.full_name
            FROM payments p JOIN users u ON u.id=p.student_id
            ORDER BY p.created_at DESC
        """).fetchall()
        return render_template("admin/payments.html", payments=rows)
    finally:
        db.close()


@admin_bp.route("/visitors")
@role_required("admin")
def visitors():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT v.*, u.full_name
            FROM visitors v JOIN users u ON u.id=v.student_id
            ORDER BY v.check_in DESC
        """).fetchall()
        return render_template("admin/visitors.html", visitors=rows)
    finally:
        db.close()


@admin_bp.route("/notices", methods=["GET", "POST"])
@role_required("admin")
def notices():
    db = get_db()
    try:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            if title and content:
                db.execute(
                    "INSERT INTO notices (title, content, created_by) VALUES (?, ?, ?)",
                    (title, content, request_user_id())
                )
                db.commit()
                flash("Notice published.", "success")
                return redirect(url_for("admin.notices"))
            flash("Title and content are required.", "danger")

        rows = db.execute(
            "SELECT * FROM notices ORDER BY created_at DESC"
        ).fetchall()
        return render_template("admin/notices.html", notices=rows)
    finally:
        db.close()


def request_user_id():
    from flask import session
    return session.get("user_id")


@admin_bp.route("/analytics")
@role_required("admin")
def analytics():
    db = get_db()
    try:
        complaint_stats = db.execute("""
            SELECT status, COUNT(*) AS total
            FROM complaints GROUP BY status
        """).fetchall()
        return render_template(
            "admin/analytics.html", complaint_stats=complaint_stats
        )
    finally:
        db.close()