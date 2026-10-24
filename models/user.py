from datetime import datetime
from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20), nullable=False, default="student"
    )
    student_id = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(20))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow
    )