from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from routes.auth import get_db, login_required, role_required

visitors_bp = Blueprint("visitors", __name__, url_prefix="/visitors")


@visitors_bp.route("/", methods=["GET", "POST"])
@role_required("admin")
def list_visitors():
    db = get_db()
    try:
        if request.method == "POST":
            name = request.form.get("visitor_name", "").strip()
            student_id = request.form.get("student_id", "").strip()
            purpose = request.form.get("purpose", "").strip()

            if name and student_id.isdigit() and purpose:
                student = db.execute(
                    "SELECT id FROM users WHERE id=? AND role='student'",
                    (int(student_id),)
                ).fetchone()
                if student:
                    db.execute("""
                        INSERT INTO visitors (visitor_name, student_id, purpose)
                        VALUES (?, ?, ?)
                    """, (name, int(student_id), purpose))
                    db.commit()
                    flash("Visitor registered.", "success")
                else:
                    flash("Student not found.", "danger")
            else:
                flash("Complete all visitor fields.", "danger")
            return redirect(url_for("visitors.list_visitors"))

        rows = db.execute("""
            SELECT v.*, u.full_name FROM visitors v
            JOIN users u ON u.id=v.student_id ORDER BY v.check_in DESC
        """).fetchall()
        return render_template("admin/visitors.html", visitors=rows)
    finally:
        db.close()


@visitors_bp.route("/<int:visitor_id>/checkout", methods=["POST"])
@role_required("admin")
def checkout(visitor_id):
    db = get_db()
    try:
        db.execute("""
            UPDATE visitors SET check_out=CURRENT_TIMESTAMP
            WHERE id=? AND check_out IS NULL
        """, (visitor_id,))
        db.commit()
        flash("Visitor checkout recorded.", "success")
    finally:
        db.close()
    return redirect(url_for("visitors.list_visitors"))