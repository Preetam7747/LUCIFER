from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, date
import sqlite3
import os
import csv
import io
import secrets
from datetime import timedelta

app = Flask(__name__)
# Use an environment-provided key for stable sessions in a deployed environment.
# The random fallback is convenient for local demos and deliberately invalidates
# sessions whenever the process restarts if no key has been configured.
app.secret_key = os.environ.get("SMARTHOSTEL_SECRET") or secrets.token_hex(32)
DB_PATH = Path(os.environ.get("SMARTHOSTEL_DB_PATH", Path(__file__).resolve().parent / "smarthostel.db"))

@contextmanager
def db():
    """Yield a SQLite connection and always close it after the transaction.

    sqlite3.Connection's built-in context manager commits or rolls back, but
    does not close the connection. Explicitly closing here prevents database
    file locks, especially when tests use a temporary database on Windows.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            student_id TEXT,
            room_id INTEGER,
            bed_label TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','warden'))
        );
        CREATE TABLE IF NOT EXISTS mess_menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_date TEXT NOT NULL UNIQUE,
            breakfast TEXT NOT NULL,
            lunch TEXT NOT NULL,
            dinner TEXT NOT NULL,
            updated_by INTEGER,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(updated_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            building TEXT NOT NULL,
            floor INTEGER NOT NULL,
            room_number TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK(capacity > 0),
            UNIQUE(building, room_number)
        );
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            room_id INTEGER NOT NULL,
            bed_label TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            UNIQUE(room_id, bed_label)
        );
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Resolved')),
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS outpasses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            departure TEXT NOT NULL,
            return_time TEXT NOT NULL,
            destination TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Rejected','Completed')),
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS mess_subscriptions (
            user_id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','opted_out','suspended')),
            fee_amount REAL NOT NULL DEFAULT 0, billing_period TEXT NOT NULL DEFAULT 'monthly', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS mess_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount REAL NOT NULL CHECK(amount >= 0),
            period TEXT NOT NULL, paid_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, note TEXT DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS utility_meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, utility_type TEXT NOT NULL CHECK(utility_type IN ('water','electricity')),
            room_id INTEGER NOT NULL, meter_code TEXT NOT NULL UNIQUE, reading_mode TEXT NOT NULL DEFAULT 'cumulative' CHECK(reading_mode IN ('cumulative','interval')),
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive','maintenance','disconnected')),
            warning_limit REAL NOT NULL DEFAULT 300, critical_limit REAL NOT NULL DEFAULT 500, unit TEXT NOT NULL,
            installed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(room_id) REFERENCES rooms(id)
        );
        CREATE TABLE IF NOT EXISTS utility_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, meter_id INTEGER NOT NULL, reading_value REAL NOT NULL CHECK(reading_value >= 0),
            consumption REAL NOT NULL DEFAULT 0 CHECK(consumption >= 0), reading_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL DEFAULT 'simulated' CHECK(source IN ('simulated','manual','hardware')), valid INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(meter_id) REFERENCES utility_meters(id)
        );
        CREATE TABLE IF NOT EXISTS utility_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, meter_id INTEGER NOT NULL, alert_type TEXT NOT NULL, severity TEXT NOT NULL,
            measured REAL NOT NULL, threshold REAL NOT NULL, message TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, resolved_at TEXT,
            FOREIGN KEY(meter_id) REFERENCES utility_meters(id)
        );
        CREATE TABLE IF NOT EXISTS utility_settings (
            utility_type TEXT PRIMARY KEY, rate REAL NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS utility_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER, action TEXT NOT NULL, details TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Add actual outpass movement timestamps without discarding older records.
        outpass_cols = {row[1] for row in con.execute("PRAGMA table_info(outpasses)").fetchall()}
        if "departed_at" not in outpass_cols:
            con.execute("ALTER TABLE outpasses ADD COLUMN departed_at TEXT")
        if "returned_at" not in outpass_cols:
            con.execute("ALTER TABLE outpasses ADD COLUMN returned_at TEXT")
        # Add newer menu fields safely to databases created by earlier versions.
        menu_cols = {row[1] for row in con.execute("PRAGMA table_info(mess_menu)").fetchall()}
        if "snacks" not in menu_cols:
            con.execute("ALTER TABLE mess_menu ADD COLUMN snacks TEXT NOT NULL DEFAULT 'Fruit or tea'")
        if "breakfast_time" not in menu_cols:
            con.execute("ALTER TABLE mess_menu ADD COLUMN breakfast_time TEXT NOT NULL DEFAULT '07:00–09:00'")
        if "lunch_time" not in menu_cols:
            con.execute("ALTER TABLE mess_menu ADD COLUMN lunch_time TEXT NOT NULL DEFAULT '12:00–14:00'")
        if "snacks_time" not in menu_cols:
            con.execute("ALTER TABLE mess_menu ADD COLUMN snacks_time TEXT NOT NULL DEFAULT '16:00–17:00'")
        if "dinner_time" not in menu_cols:
            con.execute("ALTER TABLE mess_menu ADD COLUMN dinner_time TEXT NOT NULL DEFAULT '19:00–21:00'")
        # A starter warden account for local development.
        existing = con.execute("SELECT id FROM users WHERE username='warden'").fetchone()
        if not existing:
            con.execute(
                "INSERT INTO users(name,username,email,password_hash,role) VALUES(?,?,?,?,?)",
                ("Demo Warden", "warden", "warden@example.test",
                 generate_password_hash("Warden123!"), "warden")
            )
        # A single local-development administrator. Stored as warden for compatibility with older DB constraints;
        # the login layer maps this unique username to the administrator session role.
        if not con.execute("SELECT id FROM users WHERE username='admin'").fetchone():
            con.execute("INSERT INTO users(name,username,email,password_hash,role) VALUES(?,?,?,?, 'warden')",
                        ("System Administrator", "admin", "admin@localhost.test", generate_password_hash("1")))
        con.execute("INSERT OR IGNORE INTO utility_settings(utility_type,rate) VALUES('water',0.02)")
        con.execute("INSERT OR IGNORE INTO utility_settings(utility_type,rate) VALUES('electricity',8.0)")
        # Fictional sample rooms.
        if con.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO rooms(building,floor,room_number,capacity) VALUES(?,?,?,?)",
                [("Block A", 1, "A-101", 3), ("Block A", 1, "A-102", 2),
                 ("Block A", 2, "A-201", 3), ("Block B", 1, "B-101", 2)]
            )
        # Add a sample menu for today if none exists.
        today = date.today().isoformat()
        if not con.execute("SELECT id FROM mess_menu WHERE menu_date=?", (today,)).fetchone():
            con.execute(
                "INSERT INTO mess_menu(menu_date,breakfast,lunch,dinner) VALUES(?,?,?,?)",
                (today, "Idli, sambar and fruit", "Rice, dal, vegetables and curd",
                 "Chapati, paneer curry and salad")
            )

        # Seed one clearly labelled demo meter per room and utility when missing.
        for room in con.execute("SELECT id,room_number FROM rooms").fetchall():
            for kind, unit, warn, crit in [("water", "L/day", 300, 500), ("electricity", "kWh/day", 8, 12)]:
                code = f"DEMO-{kind.upper()}-{room['room_number']}"
                if not con.execute("SELECT id FROM utility_meters WHERE meter_code=?", (code,)).fetchone():
                    con.execute("INSERT INTO utility_meters(utility_type,room_id,meter_code,unit,warning_limit,critical_limit) VALUES(?,?,?,?,?,?)",
                                (kind, room["id"], code, unit, warn, crit))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def staff_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") not in ("admin", "warden"):
            flash("You do not have permission to access that page.", "error")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper

@app.before_request
def csrf_guard():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    if request.method == "POST":
        supplied = request.form.get("_csrf_token", "")
        expected = session.get("_csrf_token", "")
        if not supplied or not expected or not secrets.compare_digest(supplied, expected):
            from flask import abort
            abort(400, description="Your form session expired or could not be verified. Refresh the page and try again.")

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year, "csrf_token": session.get("_csrf_token", "")}

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        # Public registration can only create student accounts. Wardens are created by an administrator.
        if role != "student":
            flash("Warden accounts must be created by the system administrator.", "error")
            return render_template("register.html")
        if not all([name, username, email, password, student_id]):
            flash("Please complete every required field.", "error")
            return render_template("register.html")
        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
            return render_template("register.html")
        try:
            with db() as con:
                con.execute("""INSERT INTO users(name,username,email,student_id,password_hash,role)
                               VALUES(?,?,?,?,?,'student')""",
                            (name, username, email, student_id, generate_password_hash(password)))
            flash("Registration successful. You can now sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username or email is already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Incorrect username or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = "admin" if user["username"] == "admin" else user["role"]
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    if session["role"] in ("warden", "admin"):
        with db() as con:
            stats = {
                "students": con.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
                "rooms": con.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
                "pending_complaints": con.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0],
                "pending_outpasses": con.execute("SELECT COUNT(*) FROM outpasses WHERE status='Pending'").fetchone()[0],
                "outside": con.execute("SELECT COUNT(*) FROM outpasses WHERE departed_at IS NOT NULL AND returned_at IS NULL").fetchone()[0],
                "present": max(0, con.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0] - con.execute("SELECT COUNT(*) FROM outpasses WHERE departed_at IS NOT NULL AND returned_at IS NULL").fetchone()[0]),
                "mess_paid": con.execute("SELECT COUNT(DISTINCT user_id) FROM mess_payments").fetchone()[0],
                "utility_alerts": con.execute("SELECT COUNT(*) FROM utility_alerts WHERE status='new'").fetchone()[0],
                "water_today": con.execute("SELECT COALESCE(SUM(consumption),0) FROM utility_readings rd JOIN utility_meters m ON m.id=rd.meter_id WHERE m.utility_type='water' AND date(rd.reading_at)=date('now','localtime')").fetchone()[0],
                "electricity_today": con.execute("SELECT COALESCE(SUM(consumption),0) FROM utility_readings rd JOIN utility_meters m ON m.id=rd.meter_id WHERE m.utility_type='electricity' AND date(rd.reading_at)=date('now','localtime')").fetchone()[0],
            }
            rooms = con.execute("""
                SELECT r.*, COUNT(a.id) AS occupied
                FROM rooms r LEFT JOIN allocations a ON a.room_id=r.id
                GROUP BY r.id ORDER BY r.building, r.floor, r.room_number LIMIT 6
            """).fetchall()
            recent = con.execute("""
                SELECT c.*, u.name AS student_name FROM complaints c
                JOIN users u ON u.id=c.user_id ORDER BY c.id DESC LIMIT 5
            """).fetchall()
        return render_template("warden.html", stats=stats, rooms=rooms, recent=recent)
    with db() as con:
        complaints = con.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC LIMIT 5",
                                 (session["user_id"],)).fetchall()
        today_menu = con.execute("SELECT * FROM mess_menu WHERE menu_date=?", (date.today().isoformat(),)).fetchone()
        allocation = con.execute("""
            SELECT r.building,r.floor,r.room_number,a.bed_label
            FROM allocations a JOIN rooms r ON r.id=a.room_id WHERE a.user_id=?
        """, (session["user_id"],)).fetchone()
        pending_outpasses = con.execute("SELECT COUNT(*) FROM outpasses WHERE user_id=? AND status='Pending'",
                                        (session["user_id"],)).fetchone()[0]
    return render_template("student.html", complaints=complaints, menu=today_menu,
                           allocation=allocation, pending_outpasses=pending_outpasses)

@app.route("/mess", methods=["GET", "POST"])
@login_required
def mess():
    if request.method == "POST":
        if session["role"] not in ("warden", "admin"):
            flash("Only wardens can edit the mess menu.", "error")
            return redirect(url_for("mess"))
        menu_date = request.form.get("menu_date", "")
        breakfast = request.form.get("breakfast", "").strip()
        lunch = request.form.get("lunch", "").strip()
        dinner = request.form.get("dinner", "").strip()
        snacks = request.form.get("snacks", "").strip() or "Not specified"
        breakfast_time=request.form.get("breakfast_time","07:00–09:00").strip()
        lunch_time=request.form.get("lunch_time","12:00–14:00").strip()
        snacks_time=request.form.get("snacks_time","16:00–17:00").strip()
        dinner_time=request.form.get("dinner_time","19:00–21:00").strip()
        if not all([menu_date, breakfast, lunch, dinner, breakfast_time, lunch_time, snacks_time, dinner_time]):
            flash("Fill in the date and all three meals.", "error")
        else:
            with db() as con:
                con.execute("""
                    INSERT INTO mess_menu(menu_date,breakfast,lunch,dinner,snacks,breakfast_time,lunch_time,snacks_time,dinner_time,updated_by,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                    ON CONFLICT(menu_date) DO UPDATE SET breakfast=excluded.breakfast,
                    lunch=excluded.lunch,dinner=excluded.dinner,snacks=excluded.snacks,
                    breakfast_time=excluded.breakfast_time,lunch_time=excluded.lunch_time,snacks_time=excluded.snacks_time,
                    dinner_time=excluded.dinner_time,updated_by=excluded.updated_by,updated_at=CURRENT_TIMESTAMP
                """, (menu_date, breakfast, lunch, dinner, snacks, breakfast_time, lunch_time, snacks_time, dinner_time, session["user_id"]))
            flash("Mess menu saved.", "success")
        return redirect(url_for("mess"))
    with db() as con:
        menus = con.execute("SELECT * FROM mess_menu ORDER BY menu_date DESC LIMIT 14").fetchall()
    return render_template("mess.html", menus=menus, today=date.today().isoformat())

@app.route("/rooms", methods=["GET", "POST"])
@login_required
@staff_required
def rooms():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            with db() as con:
                if action == "add_room":
                    building = request.form.get("building", "").strip()
                    floor = int(request.form.get("floor", "0"))
                    room_number = request.form.get("room_number", "").strip()
                    capacity = int(request.form.get("capacity", "0"))
                    if not building or not room_number or floor < 0 or capacity < 1 or capacity > 12:
                        raise ValueError("Enter valid building, floor, room number and capacity (1–12).")
                    con.execute("INSERT INTO rooms(building,floor,room_number,capacity) VALUES(?,?,?,?)",
                                (building, floor, room_number, capacity))
                    flash("Room added successfully.", "success")
                elif action == "allocate":
                    student_id = int(request.form.get("student_id", "0"))
                    room_id = int(request.form.get("room_id", "0"))
                    bed_label = request.form.get("bed_label", "").strip()
                    if not bed_label:
                        raise ValueError("Enter a bed label such as Bed 1.")
                    student = con.execute("SELECT id,role FROM users WHERE id=?", (student_id,)).fetchone()
                    room = con.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
                    if not student or student["role"] != "student" or not room:
                        raise ValueError("Choose a valid student and room.")
                    occupied = con.execute("SELECT COUNT(*) FROM allocations WHERE room_id=?", (room_id,)).fetchone()[0]
                    existing = con.execute("SELECT id FROM allocations WHERE user_id=?", (student_id,)).fetchone()
                    bed_taken = con.execute("SELECT id FROM allocations WHERE room_id=? AND bed_label=?",
                                             (room_id, bed_label)).fetchone()
                    if existing:
                        raise ValueError("This student already has a room allocation. Remove it before reassigning.")
                    if occupied >= room["capacity"]:
                        raise ValueError("This room is full. Choose a room with a vacant bed.")
                    if bed_taken:
                        raise ValueError("That bed is already occupied. Choose a vacant bed label.")
                    con.execute("INSERT INTO allocations(user_id,room_id,bed_label) VALUES(?,?,?)",
                                (student_id, room_id, bed_label))
                    con.execute("UPDATE users SET room_id=?, bed_label=? WHERE id=?",
                                (room_id, bed_label, student_id))
                    flash("Student allocated to the room.", "success")
                elif action == "remove_allocation":
                    allocation_id = int(request.form.get("allocation_id", "0"))
                    alloc = con.execute("SELECT user_id FROM allocations WHERE id=?", (allocation_id,)).fetchone()
                    if alloc:
                        con.execute("UPDATE users SET room_id=NULL, bed_label=NULL WHERE id=?", (alloc["user_id"],))
                        con.execute("DELETE FROM allocations WHERE id=?", (allocation_id,))
                    flash("Room allocation removed.", "success")
        except (ValueError, sqlite3.IntegrityError) as exc:
            flash(str(exc) if isinstance(exc, ValueError) else "That room number or bed assignment already exists.", "error")
        return redirect(url_for("rooms"))
    q = request.args.get("q", "").strip()
    with db() as con:
        students = con.execute("""
            SELECT u.id,u.name,u.student_id,u.email,a.id AS allocation_id,a.bed_label,
                   r.building,r.floor,r.room_number,r.id AS room_id
            FROM users u LEFT JOIN allocations a ON a.user_id=u.id
            LEFT JOIN rooms r ON r.id=a.room_id
            WHERE u.role='student' AND (u.name LIKE ? OR u.student_id LIKE ? OR r.room_number LIKE ? OR r.building LIKE ?)
            ORDER BY u.name
        """, tuple([f"%{q}%"]*4)).fetchall()
        room_rows = con.execute("""
            SELECT r.*, COUNT(a.id) AS occupied
            FROM rooms r LEFT JOIN allocations a ON a.room_id=r.id
            GROUP BY r.id ORDER BY r.building,r.floor,r.room_number
        """).fetchall()
        all_students = con.execute("SELECT id,name,student_id FROM users WHERE role='student' ORDER BY name").fetchall()
        allocations = con.execute("""
            SELECT a.id,a.bed_label,u.name,u.student_id,r.building,r.floor,r.room_number
            FROM allocations a JOIN users u ON u.id=a.user_id JOIN rooms r ON r.id=a.room_id
            ORDER BY r.building,r.floor,r.room_number,a.bed_label
        """).fetchall()
    return render_template("rooms.html", rooms=room_rows, students=students,
                           all_students=all_students, allocations=allocations, q=q)

@app.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():
    if request.method == "POST":
        if session["role"] != "student":
            flash("Only students can submit complaints.", "error")
            return redirect(url_for("complaints"))
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not category or not description:
            flash("Complete all complaint fields.", "error")
        else:
            with db() as con:
                con.execute("INSERT INTO complaints(user_id,title,category,description,created_at) VALUES(?,?,?,?,?)",
                            (session["user_id"], title, category, description, datetime.now().strftime("%Y-%m-%d %H:%M")))
            flash("Complaint submitted.", "success")
        return redirect(url_for("complaints"))
    with db() as con:
        if session["role"] in ("warden", "admin"):
            rows = con.execute("""SELECT c.*,u.name AS student_name,u.student_id FROM complaints c
                                  JOIN users u ON u.id=c.user_id ORDER BY c.id DESC""").fetchall()
        else:
            rows = con.execute("SELECT *, NULL AS student_name, NULL AS student_id FROM complaints WHERE user_id=? ORDER BY id DESC",
                               (session["user_id"],)).fetchall()
    return render_template("complaints.html", complaints=rows)

@app.route("/complaints/<int:complaint_id>/status", methods=["POST"])
@login_required
@staff_required
def complaint_status(complaint_id):
    status = request.form.get("status")
    if status not in ("Pending", "In Progress", "Resolved"):
        flash("Invalid complaint status.", "error")
    else:
        with db() as con:
            con.execute("UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
        flash("Complaint status updated.", "success")
    return redirect(url_for("complaints"))

@app.route("/outpass", methods=["GET", "POST"])
@login_required
def outpass():
    if request.method == "POST":
        if session["role"] != "student":
            flash("Only students can request an outpass.", "error")
            return redirect(url_for("outpass"))
        departure = request.form.get("departure", "")
        return_time = request.form.get("return_time", "")
        destination = request.form.get("destination", "").strip()
        reason = request.form.get("reason", "").strip()
        if not all([departure, return_time, destination, reason]):
            flash("Complete all outpass fields.", "error")
        elif return_time <= departure:
            flash("Return time must be after departure time.", "error")
        else:
            with db() as con:
                con.execute("""INSERT INTO outpasses(user_id,departure,return_time,destination,reason,created_at)
                               VALUES(?,?,?,?,?,?)""",
                            (session["user_id"], departure, return_time, destination, reason,
                             datetime.now().strftime("%Y-%m-%d %H:%M")))
            flash("Outpass request submitted.", "success")
        return redirect(url_for("outpass"))
    with db() as con:
        if session["role"] in ("warden", "admin"):
            rows = con.execute("""SELECT o.*,u.name AS student_name,u.student_id FROM outpasses o
                                  JOIN users u ON u.id=o.user_id ORDER BY o.id DESC""").fetchall()
        else:
            rows = con.execute("SELECT *, NULL AS student_name, NULL AS student_id FROM outpasses WHERE user_id=? ORDER BY id DESC",
                               (session["user_id"],)).fetchall()
    return render_template("outpass.html", outpasses=rows)

@app.route("/outpass/<int:outpass_id>/status", methods=["POST"])
@login_required
@staff_required
def outpass_status(outpass_id):
    status = request.form.get("status")
    if status not in ("Approved", "Rejected", "Completed"):
        flash("Invalid outpass status.", "error")
    else:
        with db() as con:
            if status == "Completed":
                con.execute("UPDATE outpasses SET status=?,returned_at=COALESCE(returned_at,CURRENT_TIMESTAMP) WHERE id=?", (status, outpass_id))
            else:
                con.execute("UPDATE outpasses SET status=? WHERE id=?", (status, outpass_id))
        flash("Outpass status updated.", "success")
    return redirect(url_for("outpass"))

@app.route("/outpass/<int:outpass_id>/event", methods=["POST"])
@login_required
@staff_required
def outpass_event(outpass_id):
    event=request.form.get("event")
    with db() as con:
        row=con.execute("SELECT * FROM outpasses WHERE id=?",(outpass_id,)).fetchone()
        if not row:
            flash("Outpass not found.","error")
        elif row["status"] != "Approved" and not row["departed_at"]:
            flash("Approve the outpass before recording departure.","error")
        elif event == "depart" and not row["departed_at"]:
            con.execute("UPDATE outpasses SET departed_at=CURRENT_TIMESTAMP WHERE id=?",(outpass_id,))
            flash("Departure recorded. Occupancy summary updated.","success")
        elif event == "return" and row["departed_at"] and not row["returned_at"]:
            con.execute("UPDATE outpasses SET returned_at=CURRENT_TIMESTAMP,status='Completed' WHERE id=?",(outpass_id,))
            flash("Return recorded. Occupancy summary updated.","success")
        else:
            flash("This movement event is not valid for the current outpass state.","error")
    return redirect(url_for("outpass"))

@app.route("/utilities/<utility_type>")
@login_required
def utilities(utility_type):
    if utility_type not in ("water", "electricity"):
        return redirect(url_for("dashboard"))
    is_admin = session.get("role") == "admin"
    is_staff = session.get("role") in ("admin", "warden")
    has_room_allocation = is_staff
    with db() as con:
        if is_staff:
            rows = con.execute("""SELECT m.*,r.building,r.floor,r.room_number,
                (SELECT COALESCE(SUM(consumption),0) FROM utility_readings x WHERE x.meter_id=m.id AND date(x.reading_at)=date('now','localtime')) AS today_usage,
                (SELECT reading_at FROM utility_readings x WHERE x.meter_id=m.id ORDER BY id DESC LIMIT 1) AS last_reading
                FROM utility_meters m JOIN rooms r ON r.id=m.room_id WHERE m.utility_type=? ORDER BY r.building,r.floor,r.room_number""", (utility_type,)).fetchall()
            alerts = con.execute("""SELECT a.*,m.meter_code,m.room_id,r.room_number,r.building,
                GROUP_CONCAT(u.name, ', ') AS student_names FROM utility_alerts a JOIN utility_meters m ON m.id=a.meter_id
                JOIN rooms r ON r.id=m.room_id LEFT JOIN allocations al ON al.room_id=r.id LEFT JOIN users u ON u.id=al.user_id
                WHERE m.utility_type=? GROUP BY a.id ORDER BY CASE a.status WHEN 'new' THEN 0 ELSE 1 END,a.id DESC LIMIT 100""", (utility_type,)).fetchall()
            rate = con.execute("SELECT rate FROM utility_settings WHERE utility_type=?", (utility_type,)).fetchone()[0]
            rooms = con.execute("SELECT id,building,room_number FROM rooms ORDER BY building,room_number").fetchall()
        else:
            assigned = con.execute("SELECT room_id FROM allocations WHERE user_id=?", (session["user_id"],)).fetchone()
            has_room_allocation = assigned is not None
            room_id = assigned["room_id"] if assigned else -1
            rows = con.execute("""SELECT m.*,r.building,r.floor,r.room_number,
                (SELECT COALESCE(SUM(consumption),0) FROM utility_readings x WHERE x.meter_id=m.id AND date(x.reading_at)=date('now','localtime')) AS today_usage,
                (SELECT reading_at FROM utility_readings x WHERE x.meter_id=m.id ORDER BY id DESC LIMIT 1) AS last_reading
                FROM utility_meters m JOIN rooms r ON r.id=m.room_id WHERE m.utility_type=? AND m.room_id=? ORDER BY m.id""", (utility_type,room_id)).fetchall()
            alerts=[]; rooms=[]
            setting=con.execute("SELECT rate FROM utility_settings WHERE utility_type=?",(utility_type,)).fetchone()
            rate=setting["rate"] if setting else 0
    return render_template("utilities.html", utility_type=utility_type, meters=rows, alerts=alerts,
                           rate=rate, rooms=rooms, is_admin=is_admin, is_staff=is_staff,
                           unit="litres" if utility_type=="water" else "kWh")

@app.route("/water-management")
@login_required
def water_management():
    """Dedicated water-management webpage for all signed-in roles."""
    return utilities("water")

@app.route("/electricity-management")
@login_required
def electricity_management():
    """Dedicated electricity-management webpage for all signed-in roles."""
    return utilities("electricity")

@app.route("/utilities/<utility_type>/meter", methods=["POST"])
@login_required
@role_required("admin")
def utility_add_meter(utility_type):
    if utility_type not in ("water", "electricity"):
        return redirect(url_for("dashboard"))
    try:
        room_id=int(request.form.get("room_id", "0")); code=request.form.get("meter_code", "").strip()
        warn=float(request.form.get("warning_limit", "0")); crit=float(request.form.get("critical_limit", "0"))
        if not code or warn <= 0 or crit < warn: raise ValueError("Enter a meter code and valid thresholds (critical must be at least warning).")
        with db() as con:
            room=con.execute("SELECT id FROM rooms WHERE id=?",(room_id,)).fetchone()
            if not room: raise ValueError("Choose a valid room.")
            unit="L/day" if utility_type=="water" else "kWh/day"
            con.execute("INSERT INTO utility_meters(utility_type,room_id,meter_code,unit,warning_limit,critical_limit) VALUES(?,?,?,?,?,?)",(utility_type,room_id,code,unit,warn,crit))
            con.execute("INSERT INTO utility_audit(actor_id,action,details) VALUES(?,?,?)",(session["user_id"],"meter_created",f"{utility_type} meter {code}"))
        flash("Meter added.","success")
    except (ValueError,sqlite3.IntegrityError) as exc:
        flash(str(exc) if isinstance(exc,ValueError) else "That meter code already exists.","error")
    return redirect(url_for("utilities",utility_type=utility_type))

@app.route("/utilities/<utility_type>/meter/<int:meter_id>/thresholds", methods=["POST"])
@login_required
@role_required("admin")
def utility_update_thresholds(utility_type, meter_id):
    if utility_type not in ("water", "electricity"):
        return redirect(url_for("dashboard"))
    try:
        warning=float(request.form.get("warning_limit", "0")); critical=float(request.form.get("critical_limit", "0"))
        if warning <= 0 or critical < warning:
            raise ValueError("Thresholds must be positive and critical must be at least warning.")
        with db() as con:
            meter=con.execute("SELECT id FROM utility_meters WHERE id=? AND utility_type=?",(meter_id,utility_type)).fetchone()
            if not meter: raise ValueError("Meter not found.")
            con.execute("UPDATE utility_meters SET warning_limit=?,critical_limit=? WHERE id=?",(warning,critical,meter_id))
            con.execute("INSERT INTO utility_audit(actor_id,action,details) VALUES(?,?,?)",(session["user_id"],"thresholds_changed",f"Meter {meter_id}: warning={warning}, critical={critical}"))
        flash("Thresholds updated.","success")
    except ValueError as exc: flash(str(exc),"error")
    return redirect(url_for("utilities",utility_type=utility_type))

@app.route("/utilities/<utility_type>/reading", methods=["POST"])
@login_required
@role_required("admin")
def utility_add_reading(utility_type):
    if utility_type not in ("water", "electricity"):
        return redirect(url_for("dashboard"))
    try:
        meter_id=int(request.form.get("meter_id","0")); value=float(request.form.get("reading_value","-1"))
        source=request.form.get("source","manual")
        if value < 0 or source not in ("manual","simulated"): raise ValueError("Enter a valid non-negative reading.")
        with db() as con:
            meter=con.execute("SELECT * FROM utility_meters WHERE id=? AND utility_type=?",(meter_id,utility_type)).fetchone()
            if not meter: raise ValueError("Choose a valid meter.")
            previous=con.execute("SELECT reading_value FROM utility_readings WHERE meter_id=? AND valid=1 ORDER BY id DESC LIMIT 1",(meter_id,)).fetchone()
            if meter["reading_mode"]=="cumulative":
                if previous and value < previous["reading_value"]:
                    raise ValueError("This cumulative reading is lower than the previous reading. Record a meter replacement/reset separately.")
                consumption=value-(previous["reading_value"] if previous else 0)
            else: consumption=value
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            con.execute("INSERT INTO utility_readings(meter_id,reading_value,consumption,reading_at,source) VALUES(?,?,?,?,?)",(meter_id,value,consumption,now,source))
            # Evaluate daily total after inserting the reading.
            daily=con.execute("SELECT COALESCE(SUM(consumption),0) FROM utility_readings WHERE meter_id=? AND date(reading_at)=date('now','localtime') AND valid=1",(meter_id,)).fetchone()[0]
            if daily >= meter["critical_limit"]: severity="critical"; threshold=meter["critical_limit"]
            elif daily >= meter["warning_limit"]: severity="warning"; threshold=meter["warning_limit"]
            else: severity=None
            if severity:
                duplicate=con.execute("SELECT id FROM utility_alerts WHERE meter_id=? AND date(created_at)=date('now','localtime') AND severity=? AND status='new'",(meter_id,severity)).fetchone()
                if not duplicate:
                    label="Water" if utility_type=="water" else "Electricity"
                    msg=f"{label} daily consumption {daily:g} {meter['unit']} crossed the {severity} threshold."
                    con.execute("INSERT INTO utility_alerts(meter_id,alert_type,severity,measured,threshold,message) VALUES(?,?,?,?,?,?)",(meter_id,"threshold_exceeded",severity,daily,threshold,msg))
            con.execute("INSERT INTO utility_audit(actor_id,action,details) VALUES(?,?,?)",(session["user_id"],"reading_added",f"Meter {meter['meter_code']}: {value} ({source})"))
        flash(f"Reading saved. Calculated consumption: {consumption:g} {meter['unit']}.","success")
    except (ValueError,sqlite3.IntegrityError) as exc:
        flash(str(exc),"error")
    return redirect(url_for("utilities",utility_type=utility_type))

@app.route("/utilities/<utility_type>/settings", methods=["POST"])
@login_required
@role_required("admin")
def utility_settings(utility_type):
    if utility_type not in ("water", "electricity"):
        return redirect(url_for("dashboard"))
    try:
        rate=float(request.form.get("rate","0"))
        if rate < 0: raise ValueError("Rate cannot be negative.")
        with db() as con:
            con.execute("INSERT INTO utility_settings(utility_type,rate,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(utility_type) DO UPDATE SET rate=excluded.rate,updated_at=CURRENT_TIMESTAMP",(utility_type,rate))
            con.execute("INSERT INTO utility_audit(actor_id,action,details) VALUES(?,?,?)",(session["user_id"],"tariff_changed",f"{utility_type} rate set to {rate}"))
        flash("Estimated cost rate updated.","success")
    except ValueError as exc: flash(str(exc),"error")
    return redirect(url_for("utilities",utility_type=utility_type))

@app.route("/utility-alerts/<int:alert_id>/status", methods=["POST"])
@login_required
@role_required("admin")
def utility_alert_status(alert_id):
    status=request.form.get("status")
    if status not in ("acknowledged","investigating","resolved","dismissed"):
        flash("Invalid alert status.","error")
    else:
        with db() as con:
            con.execute("UPDATE utility_alerts SET status=?,resolved_at=CASE WHEN ? IN ('resolved','dismissed') THEN CURRENT_TIMESTAMP ELSE resolved_at END WHERE id=?",(status,status,alert_id))
            con.execute("INSERT INTO utility_audit(actor_id,action,details) VALUES(?,?,?)",(session["user_id"],"alert_status_changed",f"Alert {alert_id}: {status}"))
        flash("Alert updated.","success")
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/mess-records", methods=["GET","POST"])
@login_required
@role_required("admin")
def mess_records():
    if request.method=="POST":
        action=request.form.get("action")
        try:
            user_id=int(request.form.get("user_id","0"))
            with db() as con:
                student=con.execute("SELECT id FROM users WHERE id=? AND role='student'",(user_id,)).fetchone()
                if not student: raise ValueError("Choose a valid student.")
                if action=="subscription":
                    status=request.form.get("status","active"); fee=float(request.form.get("fee_amount","0"))
                    if status not in ("active","opted_out","suspended") or fee<0: raise ValueError("Invalid subscription details.")
                    con.execute("INSERT INTO mess_subscriptions(user_id,status,fee_amount) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET status=excluded.status,fee_amount=excluded.fee_amount,updated_at=CURRENT_TIMESTAMP",(user_id,status,fee))
                elif action=="payment":
                    amount=float(request.form.get("amount","0")); period=request.form.get("period","monthly").strip(); note=request.form.get("note","").strip()
                    if amount<=0 or not period: raise ValueError("Enter a positive payment and billing period.")
                    con.execute("INSERT INTO mess_payments(user_id,amount,period,note) VALUES(?,?,?,?)",(user_id,amount,period,note))
                else: raise ValueError("Unknown action.")
            flash("Mess record saved.","success")
        except (ValueError,sqlite3.IntegrityError) as exc: flash(str(exc),"error")
        return redirect(url_for("mess_records"))
    with db() as con:
        students=con.execute("""SELECT u.id,u.name,u.student_id,r.room_number,
            COALESCE(ms.status,'active') AS mess_status,COALESCE(ms.fee_amount,0) AS fee_amount,
            COALESCE((SELECT SUM(p.amount) FROM mess_payments p WHERE p.user_id=u.id),0) AS paid_total,
            (SELECT MAX(p.paid_on) FROM mess_payments p WHERE p.user_id=u.id) AS last_paid
            FROM users u LEFT JOIN allocations a ON a.user_id=u.id LEFT JOIN rooms r ON r.id=a.room_id
            LEFT JOIN mess_subscriptions ms ON ms.user_id=u.id WHERE u.role='student' ORDER BY u.name""").fetchall()
    return render_template("mess_records.html",students=students)

@app.route("/reports/utility.csv")
@login_required
@role_required("admin")
def utility_csv():
    kind=request.args.get("type","water")
    if kind not in ("water","electricity"): kind="water"
    with db() as con:
        rows=con.execute("""SELECT m.utility_type,m.meter_code,r.building,r.floor,r.room_number,rd.reading_value,rd.consumption,rd.reading_at,rd.source,m.unit
            FROM utility_readings rd JOIN utility_meters m ON m.id=rd.meter_id JOIN rooms r ON r.id=m.room_id WHERE m.utility_type=? ORDER BY rd.reading_at DESC""",(kind,)).fetchall()
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(["utility","meter","block","floor","room","reading","consumption","timestamp","source","unit"])
    for row in rows: writer.writerow(list(row))
    from flask import Response
    return Response(output.getvalue(),mimetype="text/csv",headers={"Content-Disposition":f"attachment; filename={kind}_readings.csv"})

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

init_db()

if __name__ == "__main__":
    # Debug mode is opt-in: set FLASK_DEBUG=1 only during local development.
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
