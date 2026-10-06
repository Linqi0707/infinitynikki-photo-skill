import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def get_all_photos():
    """查询全部照片"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM photos
        ORDER BY shoot_time DESC
    """)

    photos = cursor.fetchall()
    conn.close()

    return photos


def search_by_date(date):
    """根据日期查询照片，例如：2026-10-03"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM photos
        WHERE shoot_time LIKE ?
        ORDER BY shoot_time
    """, (f"{date}%",))

    photos = cursor.fetchall()
    conn.close()

    return photos


def get_photo_by_id(photo_id):
    """根据photo_id查询照片"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM photos
        WHERE photo_id = ?
    """, (photo_id,))

    photo = cursor.fetchone()
    conn.close()

    return photo


def print_photos(photos):
    """打印照片信息"""
    if not photos:
        print("没有找到照片")
        return

    for photo in photos:
        print("-" * 50)
        print(f"photo_id   : {photo['photo_id']}")
        print(f"filename   : {photo['filename']}")
        print(f"shoot_time : {photo['shoot_time']}")
        print(f"path       : {photo['path']}")
        print(f"size       : {photo['width']} x {photo['height']}")
        print(f"sha256     : {photo['sha256'][:16]}...")


def main():
    print("========== 查询全部照片 ==========")

    photos = get_all_photos()
    print(f"数据库共有 {len(photos)} 张照片")

    print_photos(photos[:5])

    print("\n========== 按日期查询 ==========")

    photos = search_by_date("2026-10-03")
    print(f"2026-10-03 共 {len(photos)} 张照片")

    print_photos(photos)


if __name__ == "__main__":
    main()