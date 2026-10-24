from flask import Blueprint, render_template
from routes.auth import get_db, login_required

mess_bp = Blueprint("mess", __name__, url_prefix="/mess")


@mess_bp.route("/")
@login_required
def menu():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM mess_menu ORDER BY meal_date, meal_type"
        ).fetchall()
        return render_template("student/mess.html", menu=rows)
    finally:
        db.close()