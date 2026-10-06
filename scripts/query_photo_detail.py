import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def query_photo(filename):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM photos
        WHERE filename=?
    """, (filename,))

    photo = cursor.fetchone()

    if not photo:
        conn.close()
        return None


    photo_id = photo["photo_id"]


    cursor.execute("""
        SELECT *
        FROM photo_semantics
        WHERE photo_id=?
    """, (photo_id,))

    semantic = cursor.fetchone()


    cursor.execute("""
        SELECT *
        FROM outfits
        WHERE photo_id=?
    """, (photo_id,))

    outfit = cursor.fetchone()


    cursor.execute("""
        SELECT *
        FROM camera_params
        WHERE photo_id=?
    """, (photo_id,))

    camera = cursor.fetchone()


    result = {
        "photo": dict(photo),
        "semantic": dict(semantic) if semantic else None,
        "outfit": dict(outfit) if outfit else None,
        "camera": dict(camera) if camera else None
    }


    conn.close()

    return result



def main():

    filename = input(
        "请输入照片文件名: "
    ).strip()


    result = query_photo(
        filename
    )


    if not result:

        print(
            "未找到照片"
        )

        return


    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()