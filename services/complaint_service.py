def create_complaint(
    db,
    student_id,
    title,
    description,
    category="other"
):
    cursor = db.execute("""
        INSERT INTO complaints
        (student_id, title, description, category)
        VALUES (?, ?, ?, ?)
    """, (
        student_id,
        title,
        description,
        category
    ))

    db.commit()
    return cursor.lastrowid


def get_student_complaints(db, student_id):
    return db.execute("""
        SELECT *
        FROM complaints
        WHERE student_id = ?
        ORDER BY created_at DESC
    """, (student_id,)).fetchall()


def get_all_complaints(db):
    return db.execute("""
        SELECT
            c.*,
            u.full_name,
            u.student_id AS student_number
        FROM complaints c
        JOIN users u
            ON c.student_id = u.id
        ORDER BY c.created_at DESC
    """).fetchall()


def get_complaint(db, complaint_id):
    return db.execute("""
        SELECT *
        FROM complaints
        WHERE id = ?
    """, (complaint_id,)).fetchone()


def update_complaint_status(db, complaint_id, status):
    allowed = {
        "pending",
        "in_progress",
        "resolved",
        "rejected"
    }

    if status not in allowed:
        return False

    db.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    db.commit()
    return True


def delete_complaint(db, complaint_id):
    db.execute("""
        DELETE FROM complaints
        WHERE id = ?
    """, (complaint_id,))

    db.commit()