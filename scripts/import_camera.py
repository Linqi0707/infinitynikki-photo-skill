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


def save_camera(photo_id, camera_code, description=None):
    """保存摄影参数编码"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO camera_params
        (
            photo_id,
            camera_code,
            description
        )
        VALUES (?, ?, ?)
    """, (
        photo_id,
        camera_code,
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
        print("未找到照片")
        return

    print(
        f"找到照片: {photo_id}"
    )

    camera_code = input(
        "请输入摄影参数编码: "
    ).strip()

    if not camera_code:
        print("摄影参数不能为空")
        return

    description = input(
        "请输入备注(可为空): "
    ).strip()


    save_camera(
        photo_id,
        camera_code,
        description
    )

    print(
        "摄影参数保存成功"
    )


if __name__ == "__main__":
    main()