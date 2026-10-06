import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "infinitynikki_photos.db"


def get_pending_photos(limit=10):
    """获取待分析照片"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM photos
        WHERE analysis_status IN ('pending','failed')
        LIMIT ?
    """, (limit,))

    photos = cursor.fetchall()

    conn.close()

    return photos



def save_photo_semantics(photo_id, semantics):
    """保存VLM分析结果"""

    print("准备保存语义:")
    print(semantics)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO photo_semantics
        (
            photo_id,
            photo_type,
            portrait_framing,
            portrait_view,
            scene_category,
            game_time,
            color_tone,
            background
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        photo_id,
        semantics.get("photo_type"),
        semantics.get("portrait_framing"),
        semantics.get("portrait_view"),
        semantics.get("scene_category"),
        semantics.get("game_time"),
        semantics.get("color_tone"),
        semantics.get("background")
    ))

    conn.commit()
    conn.close()

    print(
        f"语义保存成功: {photo_id}"
    )



def update_analysis_status(photo_id, status):
    """更新照片分析状态"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE photos
        SET analysis_status=?
        WHERE photo_id=?
    """, (
        status,
        photo_id
    ))

    conn.commit()
    conn.close()