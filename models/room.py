from datetime import datetime
from database import db


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(30), unique=True, nullable=False)
    block_name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    monthly_fee = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(
        db.String(30), nullable=False, default="available"
    )


class RoomAllocation(db.Model):
    __tablename__ = "room_allocations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    room_id = db.Column(
        db.Integer, db.ForeignKey("rooms.id"), nullable=False
    )
    allocated_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )
    status = db.Column(
        db.String(20), nullable=False, default="active"
    )