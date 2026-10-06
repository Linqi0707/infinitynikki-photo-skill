import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def get_photo_id(filename):
    """根据照片文件名查询photo_id"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT photo_id
        FROM photos
        WHERE filename=?
    """, (filename,))

    result = cursor.fetchone()

    conn.close()

    return result["photo_id"] if result else None


def add_outfit(photo_id, outfit_code, description=None):
    """保存搭配码"""

    if not outfit_code.endswith("#"):
        raise ValueError(
            "搭配码格式错误，应以#结尾"
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO outfits
        (
            photo_id,
            outfit_code,
            outfit_description
        )
        VALUES (?, ?, ?)
    """, (
        photo_id,
        outfit_code,
        description
    ))

    conn.commit()
    conn.close()


def main():

    filename = input(
        "请输入照片文件名: "
    ).strip()

    photo_id = get_photo_id(
        filename
    )

    if not photo_id:
        print(
            "未找到该照片"
        )
        return


    print(
        f"找到照片: {photo_id}"
    )


    outfit_code = input(
        "请输入搭配码: "
    ).strip()


    description = input(
        "请输入搭配描述(可为空): "
    ).strip()


    try:

        add_outfit(
            photo_id,
            outfit_code,
            description
        )

        print(
            "搭配码保存成功"
        )

    except Exception as e:

        print(
            f"保存失败: {e}"
        )


if __name__ == "__main__":
    main()