def get_all_rooms(db):
    return db.execute("""
        SELECT
            r.id,
            r.room_number,
            r.block_name,
            r.capacity,
            r.monthly_fee,
            r.status,
            COUNT(ra.id) AS occupied_beds
        FROM rooms r
        LEFT JOIN room_allocations ra
            ON r.id = ra.room_id
            AND ra.status = 'active'
        GROUP BY r.id
        ORDER BY r.room_number
    """).fetchall()


def get_room(db, room_id):
    return db.execute("""
        SELECT *
        FROM rooms
        WHERE id = ?
    """, (room_id,)).fetchone()


def get_available_rooms(db):
    return db.execute("""
        SELECT
            r.*,
            COUNT(ra.id) AS occupied_beds
        FROM rooms r
        LEFT JOIN room_allocations ra
            ON r.id = ra.room_id
            AND ra.status = 'active'
        WHERE r.status = 'available'
        GROUP BY r.id
        HAVING occupied_beds < r.capacity
        ORDER BY r.room_number
    """).fetchall()


def add_room(db, room_number, block_name, capacity, monthly_fee):
    cursor = db.execute("""
        INSERT INTO rooms
        (room_number, block_name, capacity, monthly_fee, status)
        VALUES (?, ?, ?, ?, 'available')
    """, (
        room_number,
        block_name,
        capacity,
        monthly_fee
    ))

    db.commit()
    return cursor.lastrowid


def update_room_status(db, room_id, status):
    db.execute("""
        UPDATE rooms
        SET status = ?
        WHERE id = ?
    """, (status, room_id))

    db.commit()


def delete_room(db, room_id):
    db.execute("""
        DELETE FROM rooms
        WHERE id = ?
    """, (room_id,))

    db.commit()


def allocate_room(db, student_id, room_id):
    room = get_room(db, room_id)

    if not room:
        return False, "Room not found"

    if room["status"] == "maintenance":
        return False, "Room is under maintenance"

    existing = db.execute("""
        SELECT id
        FROM room_allocations
        WHERE student_id = ?
        AND status = 'active'
    """, (student_id,)).fetchone()

    if existing:
        return False, "Student already has an active room"

    occupied = db.execute("""
        SELECT COUNT(*) AS count
        FROM room_allocations
        WHERE room_id = ?
        AND status = 'active'
    """, (room_id,)).fetchone()["count"]

    if occupied >= room["capacity"]:
        db.execute("""
            UPDATE rooms
            SET status = 'full'
            WHERE id = ?
        """, (room_id,))
        db.commit()

        return False, "Room is full"

    db.execute("""
        INSERT INTO room_allocations
        (student_id, room_id, status)
        VALUES (?, ?, 'active')
    """, (student_id, room_id))

    occupied += 1

    if occupied >= room["capacity"]:
        new_status = "full"
    else:
        new_status = "available"

    db.execute("""
        UPDATE rooms
        SET status = ?
        WHERE id = ?
    """, (new_status, room_id))

    db.commit()

    return True, "Room allocated successfully"


def end_room_allocation(db, allocation_id):
    allocation = db.execute("""
        SELECT room_id
        FROM room_allocations
        WHERE id = ?
        AND status = 'active'
    """, (allocation_id,)).fetchone()

    if not allocation:
        return False

    db.execute("""
        UPDATE room_allocations
        SET status = 'ended'
        WHERE id = ?
    """, (allocation_id,))

    room = get_room(db, allocation["room_id"])

    if room and room["status"] != "maintenance":
        db.execute("""
            UPDATE rooms
            SET status = 'available'
            WHERE id = ?
        """, (allocation["room_id"],))

    db.commit()

    return True