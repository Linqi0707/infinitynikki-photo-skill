import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "infinitynikki_photos.db"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    UPDATE photos
    SET analysis_status='pending'
    WHERE analysis_status='failed'
""")

count = cursor.rowcount

conn.commit()
conn.close()

print(f"已重置 {count} 张失败照片")