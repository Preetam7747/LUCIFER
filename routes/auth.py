import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_db():
    """Open a connection to the hostel database."""
    db_path = current_app.config.get("DATABASE_PATH")

    if not db_path:
        db_path = (
            Path(current_app.root_path) / "instance" / "hostel.db"
        )

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def login_required(view):
    """Require a logged-in user before accessing a page."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    """Restrict a page to users with the specified roles."""

    def decorator(view):

        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash(
                    "You do not have permission to access this page.",
                    "danger",
                )
                return redirect(url_for("home"))

            return view(*args, **kwargs)

        return wrapped

    return decorator


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Log in an existing user."""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("auth/login.html")

        connection = get_db()

        try:
            user = connection.execute(
                """
                SELECT id, full_name, email, password_hash, role
                FROM users
                WHERE lower(email) = ?
                """,
                (email,),
            ).fetchone()
        finally:
            connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            flash("Login successful!", "success")

            if user["role"] == "admin":
                return redirect(url_for("admin.dashboard"))

            if user["role"] == "staff":
                return redirect(url_for("staff.dashboard"))

            return redirect(url_for("student.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new student account."""

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        student_id = request.form.get("student_id", "").strip() or None
        phone = request.form.get("phone", "").strip()

        if not full_name or not email or not password:
            flash(
                "Please fill in your name, email, and password.",
                "danger",
            )
            return render_template("auth/register.html")

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger",
            )
            return render_template("auth/register.html")

        connection = get_db()

        try:
            connection.execute(
                """
                INSERT INTO users
                    (full_name, email, password_hash, role, student_id, phone)
                VALUES (?, ?, ?, 'student', ?, ?)
                """,
                (
                    full_name,
                    email,
                    generate_password_hash(password),
                    student_id,
                    phone or None,
                ),
            )
            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()
            flash(
                "That email or student ID is already registered.",
                "danger",
            )
            return render_template("auth/register.html")

        finally:
            connection.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Log out the current user."""

    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))