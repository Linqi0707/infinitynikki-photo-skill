import sys
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PHOTO_DIR = (
    PROJECT_ROOT /
    "data" /
    "photos"
)

OUTPUT_FILE = (
    PROJECT_ROOT /
    "data" /
    "photos_metadata.json"
)


sys.path.append(
    str(PROJECT_ROOT)
)

from src.database import get_connection


FILENAME_PATTERN = re.compile(
    r"^(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d+)$"
)



def parse_filename(file_path):

    stem = file_path.stem

    match = FILENAME_PATTERN.match(
        stem
    )

    if not match:
        return None, None


    year, month, day, hour, minute, second, suffix = match.groups()


    shoot_time = datetime(
        int(year),
        int(month),
        int(day),
        int(hour),
        int(minute),
        int(second)
    )


    return shoot_time, suffix



def calculate_sha256(file_path):

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as f:

        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()



def scan_photos():

    photos = []

    count = 0


    for file_path in PHOTO_DIR.rglob("*"):

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() != ".jpeg":
            continue


        count += 1


        shoot_time, suffix_id = parse_filename(
            file_path
        )


        try:

            with Image.open(file_path) as img:

                width, height = img.size


        except Exception as e:

            print(
                f"图片读取失败:{file_path.name}"
            )

            continue



        if width > height:
            orientation = "landscape"

        elif height > width:
            orientation = "portrait"

        else:
            orientation = "square"



        photo = {

            "filename":
                file_path.name,

            "path":
                str(
                    file_path.relative_to(
                        PROJECT_ROOT
                    )
                ),

            "shoot_time":
                shoot_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if shoot_time else None,


            "suffix_id":
                suffix_id,


            "width":
                width,


            "height":
                height,


            "orientation":
                orientation,


            "sha256":
                calculate_sha256(
                    file_path
                )
        }


        photos.append(photo)



    print(
        f"扫描发现 {count} 张图片"
    )


    return photos



def save_database(photos):

    conn = get_connection()

    cursor = conn.cursor()


    new_count = 0


    for photo in photos:


        photo_id = (
            "photo_"
            +
            photo["sha256"][:12]
        )


        try:

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
                    sha256
                )
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                photo_id,
                photo["filename"],
                photo["path"],
                photo["shoot_time"],
                photo["suffix_id"],
                photo["width"],
                photo["height"],
                photo["orientation"],
                photo["sha256"]
            ))


            if cursor.rowcount:
                new_count += 1


        except Exception as e:

            print(
                f"保存失败:{photo['filename']}"
            )

            print(e)



    conn.commit()
    conn.close()


    return new_count



def main():

    photos = scan_photos()


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            photos,
            f,
            ensure_ascii=False,
            indent=2
        )


    count = save_database(
        photos
    )


    print(
        f"新增数据库照片:{count}张"
    )


if __name__ == "__main__":
    main()