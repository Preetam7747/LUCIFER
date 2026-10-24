import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "instance"
DATABASE_PATH = DATABASE_DIR / "hostel.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def initialize_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        rooms = [
            ("A101", "Block A", 4, 5000),
            ("A102", "Block A", 4, 5000),
            ("B201", "Block B", 3, 6000),
            ("B202", "Block B", 3, 6000),
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO rooms
            (room_number, block_name, capacity, monthly_fee)
            VALUES (?, ?, ?, ?)
            """,
            rooms,
        )

        connection.commit()
        print("Database initialized successfully!")
        print(f"Database location: {DATABASE_PATH}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()