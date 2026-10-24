import sqlite3

from flask import Flask, render_template, g
from config import Config
from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp
from routes.rooms import rooms_bp
from routes.complaints import complaints_bp
from routes.leave import leave_bp
from routes.mess import mess_bp
from routes.payments import payments_bp
from routes.visitors import visitors_bp
from routes.api import api_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(complaints_bp)
app.register_blueprint(leave_bp)
app.register_blueprint(mess_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(visitors_bp)
app.register_blueprint(api_bp)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return {"status": "ok", "application": "SmartHostel"}


if __name__ == "__main__":
    app.run(debug=True)