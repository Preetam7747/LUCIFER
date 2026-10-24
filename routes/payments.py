from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from routes.auth import get_db, login_required, role_required

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/")
@login_required
def list_payments():
    db = get_db()
    try:
        if session.get("role") == "admin":
            rows = db.execute("""
                SELECT p.*, u.full_name FROM payments p
                JOIN users u ON u.id=p.student_id ORDER BY p.created_at DESC
            """).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM payments WHERE student_id=? ORDER BY created_at DESC",
                (session["user_id"],)
            ).fetchall()
        return render_template("student/payments.html", payments=rows)
    finally:
        db.close()


@payments_bp.route("/create", methods=["POST"])
@role_required("admin")
def create_payment():
    try:
        student_id = int(request.form.get("student_id", "0"))
        amount = float(request.form.get("amount", "0"))
    except ValueError:
        flash("Enter valid payment details.", "danger")
        return redirect(url_for("admin.payments"))

    description = request.form.get("description", "").strip()
    if amount < 0 or not description:
        flash("Enter a valid amount and description.", "danger")
        return redirect(url_for("admin.payments"))

    db = get_db()
    try:
        db.execute("""
            INSERT INTO payments (student_id, amount, description)
            VALUES (?, ?, ?)
        """, (student_id, amount, description))
        db.commit()
        flash("Payment record created.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.payments"))


@payments_bp.route("/<int:payment_id>/mark-paid", methods=["POST"])
@role_required("admin")
def mark_paid(payment_id):
    db = get_db()
    try:
        db.execute("""
            UPDATE payments SET status='paid', paid_at=CURRENT_TIMESTAMP
            WHERE id=? AND status='pending'
        """, (payment_id,))
        db.commit()
        flash("Payment marked as paid.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.payments"))