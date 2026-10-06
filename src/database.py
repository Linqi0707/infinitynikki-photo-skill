import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "infinitynikki_photos.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            photo_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            shoot_time TEXT,
            suffix_id TEXT,
            width INTEGER,
            height INTEGER,
            orientation TEXT,
            sha256 TEXT UNIQUE NOT NULL,
            analysis_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photo_semantics (
            photo_id TEXT PRIMARY KEY,
            photo_type TEXT,
            portrait_framing TEXT,
            portrait_view TEXT,
            scene_category TEXT,
            game_time TEXT,
            color_tone TEXT,
            background TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(photo_id)
            REFERENCES photos(photo_id)
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfits (
            outfit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id TEXT NOT NULL,
            outfit_code TEXT NOT NULL,
            outfit_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(photo_id)
            REFERENCES photos(photo_id)
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS camera_params (
            camera_id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id TEXT NOT NULL,
            camera_code TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(photo_id)
            REFERENCES photos(photo_id)
        )
    """)


    conn.commit()
    conn.close()

    print("数据库初始化完成")
    print(f"数据库路径: {DB_PATH}")


if __name__ == "__main__":
    init_database()