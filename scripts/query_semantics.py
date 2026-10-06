import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def main():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.filename,
            s.photo_type,
            s.portrait_framing,
            s.portrait_view,
            s.scene_category,
            s.game_time,
            s.color_tone,
            s.background
        FROM photos p
        JOIN photo_semantics s
        ON p.photo_id=s.photo_id
        LIMIT 20
    """)

    results = cursor.fetchall()

    for item in results:
        print("-" * 40)
        print(f"照片: {item['filename']}")
        print(f"类型: {item['photo_type']}")
        print(f"构图: {item['portrait_framing']}")
        print(f"视角: {item['portrait_view']}")
        print(f"场景: {item['scene_category']}")
        print(f"游戏时间: {item['game_time']}")
        print(f"色调: {item['color_tone']}")
        print(f"背景: {item['background']}")

    conn.close()


if __name__ == "__main__":
    main()