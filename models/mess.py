from database import db


class MessMenu(db.Model):
    __tablename__ = "mess_menu"

    id = db.Column(db.Integer, primary_key=True)
    meal_date = db.Column(db.String(20), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    menu_items = db.Column(db.Text, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "meal_date", "meal_type",
            name="uq_mess_date_type"
        ),
    )