import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


PHOTO_DIR = Path(
    r"D:\infinityNikki\InfinityNikki Launcher\InfinityNikki\X6Game\Saved\GamePlayPhotos\100248472\NikkiPhotos_HighQuality"
)


def scan_game_photos():
    photos = {}

    for file in PHOTO_DIR.rglob("*.jpeg"):
        photos[file.name] = str(file)

    print(f"游戏目录照片:{len(photos)}张")

    return photos


def migrate():

    photo_map = scan_game_photos()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT photo_id, filename, path FROM photos"
    )

    rows = cursor.fetchall()

    update_count = 0
    not_found = 0


    for row in rows:

        photo_id = row[0]
        filename = row[1]


        if filename not in photo_map:
            not_found += 1
            continue


        new_path = photo_map[filename]


        cursor.execute(
            """
            UPDATE photos
            SET path = ?
            WHERE photo_id = ?
            """,
            (
                new_path,
                photo_id
            )
        )


        update_count += 1


    conn.commit()
    conn.close()


    print(
        f"更新路径:{update_count}张"
    )

    print(
        f"未找到对应照片:{not_found}张"
    )


if __name__ == "__main__":
    migrate()