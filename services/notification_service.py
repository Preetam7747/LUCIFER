def get_dashboard_stats(db):
    students = db.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'student'
    """).fetchone()["count"]

    rooms = db.execute("""
        SELECT COUNT(*) AS count
        FROM rooms
    """).fetchone()["count"]

    occupied_beds = db.execute("""
        SELECT COUNT(*) AS count
        FROM room_allocations
        WHERE status = 'active'
    """).fetchone()["count"]

    total_capacity = db.execute("""
        SELECT COALESCE(SUM(capacity), 0) AS total
        FROM rooms
        WHERE status != 'maintenance'
    """).fetchone()["total"]

    complaints = db.execute("""
        SELECT COUNT(*) AS count
        FROM complaints
        WHERE status IN ('pending', 'in_progress')
    """).fetchone()["count"]

    pending_leaves = db.execute("""
        SELECT COUNT(*) AS count
        FROM leave_requests
        WHERE status = 'pending'
    """).fetchone()["count"]

    pending_payments = db.execute("""
        SELECT COUNT(*) AS count
        FROM payments
        WHERE status = 'pending'
    """).fetchone()["count"]

    available_beds = max(total_capacity - occupied_beds, 0)

    return {
        "total_students": students,
        "total_rooms": rooms,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "open_complaints": complaints,
        "pending_leaves": pending_leaves,
        "pending_payments": pending_payments
    }


def get_complaint_statistics(db):
    rows = db.execute("""
        SELECT status, COUNT(*) AS count
        FROM complaints
        GROUP BY status
    """).fetchall()

    return {
        row["status"]: row["count"]
        for row in rows
    }


def get_payment_statistics(db):
    rows = db.execute("""
        SELECT status, COUNT(*) AS count,
               COALESCE(SUM(amount), 0) AS total
        FROM payments
        GROUP BY status
    """).fetchall()

    return [
        {
            "status": row["status"],
            "count": row["count"],
            "total": row["total"]
        }
        for row in rows
    ]