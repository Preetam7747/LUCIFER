from flask import Blueprint, flash, redirect, render_template, request, url_for
from routes.auth import get_db, login_required, role_required

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


@rooms_bp.route("/")
@login_required
def list_rooms():
    db = get_db()
    try:
        rows = db.execute("""
            SELECT r.*,
                   (SELECT COUNT(*) FROM room_allocations a
                    WHERE a.room_id=r.id AND a.status='active') AS occupied
            FROM rooms r ORDER BY r.block_name, r.room_number
        """).fetchall()
        return render_template("admin/rooms.html", rooms=rows)
    finally:
        db.close()


@rooms_bp.route("/add", methods=["POST"])
@role_required("admin")
def add_room():
    number = request.form.get("room_number", "").strip()
    block = request.form.get("block_name", "").strip()
    try:
        capacity = int(request.form.get("capacity", "0"))
        fee = float(request.form.get("monthly_fee", "0"))
        if not number or not block or capacity < 1 or fee < 0:
            raise ValueError
    except ValueError:
        flash("Enter valid room details.", "danger")
        return redirect(url_for("admin.rooms"))

    db = get_db()
    try:
        db.execute("""
            INSERT INTO rooms (room_number, block_name, capacity, monthly_fee)
            VALUES (?, ?, ?, ?)
        """, (number, block, capacity, fee))
        db.commit()
        flash("Room added.", "success")
    except Exception:
        db.rollback()
        flash("Room number already exists or details are invalid.", "danger")
    finally:
        db.close()
    return redirect(url_for("admin.rooms"))


@rooms_bp.route("/allocate", methods=["POST"])
@role_required("admin")
def allocate_room():
    try:
        student_id = int(request.form.get("student_id", "0"))
        room_id = int(request.form.get("room_id", "0"))
    except ValueError:
        flash("Select a valid student and room.", "danger")
        return redirect(url_for("admin.allocations"))

    db = get_db()
    try:
        room = db.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
        student = db.execute(
            "SELECT id FROM users WHERE id=? AND role='student'", (student_id,)
        ).fetchone()
        occupied = db.execute("""
            SELECT COUNT(*) FROM room_allocations
            WHERE room_id=? AND status='active'
        """, (room_id,)).fetchone()[0]
        existing = db.execute("""
            SELECT id FROM room_allocations
            WHERE student_id=? AND status='active'
        """, (student_id,)).fetchone()

        if not room or not student or occupied >= room["capacity"] or existing:
            flash("Room is full, or the student already has a room.", "danger")
        else:
            db.execute("""
                INSERT INTO room_allocations (student_id, room_id)
                VALUES (?, ?)
            """, (student_id, room_id))
            db.commit()
            flash("Room allocated.", "success")
    finally:
        db.close()
    return redirect(url_for("admin.allocations"))