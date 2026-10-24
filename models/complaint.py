from datetime import datetime
from database import db


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(
        db.String(50), nullable=False, default="other"
    )
    status = db.Column(
        db.String(30), nullable=False, default="pending"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )