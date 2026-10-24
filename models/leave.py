from datetime import datetime
from database import db


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    reason = db.Column(db.Text, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    departure_time = db.Column(db.String(50), nullable=False)
    return_time = db.Column(db.String(50), nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )