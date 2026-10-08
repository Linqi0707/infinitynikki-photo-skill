import sys
import json
import hashlib
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection
from scripts.scan_photos import parse_filename
from scripts.analyze_photo import main as analyze_new_photos

CONFIG_FILE = PROJECT_ROOT / "references" / "config.json"


def load_photo_dir():
    config = json.loads(
        CONFIG_FILE.read_text(encoding="utf-8")
    )
    return Path(config["photo_dir"])


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_existing_filenames():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename
        FROM photos
    """)

    filenames = {
        row["filename"]
        for row in cursor.fetchall()
    }

    conn.close()

    return filenames


def sync_photos():
    photo_dir = load_photo_dir()
    existing = get_existing_filenames()

    conn = get_connection()
    cursor = conn.cursor()

    new_count = 0

    for file_path in photo_dir.rglob("*.jpeg"):
        if file_path.name in existing:
            continue

        shoot_time, suffix_id = parse_filename(
            file_path
        )

        try:
            with Image.open(file_path) as img:
                width, height = img.size
        except Exception:
            print(f"图片读取失败: {file_path.name}")
            continue

        if width > height:
            orientation = "landscape"
        elif height > width:
            orientation = "portrait"
        else:
            orientation = "square"

        sha256 = calculate_sha256(file_path)
        photo_id = "photo_" + sha256[:12]

        cursor.execute("""
            INSERT OR IGNORE INTO photos
            (
                photo_id,
                filename,
                path,
                shoot_time,
                suffix_id,
                width,
                height,
                orientation,
                sha256,
                analysis_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            photo_id,
            file_path.name,
            str(file_path),
            shoot_time.strftime("%Y-%m-%d %H:%M:%S")
            if shoot_time else None,
            suffix_id,
            width,
            height,
            orientation,
            sha256
        ))

        if cursor.rowcount:
            new_count += 1
            print(f"新增: {file_path.name}")

    conn.commit()
    conn.close()

    return new_count


def main():
    count = sync_photos()

    print(f"\n发现新增照片: {count} 张")

    if count == 0:
        print("没有需要同步的新照片")
        return

    print("\n开始分析新增照片...\n")

    analyze_new_photos()


if __name__ == "__main__":
    main()