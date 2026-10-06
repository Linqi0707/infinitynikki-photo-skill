import argparse
import json
import sqlite3
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "references" / "local_config.json"


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"找不到配置文件: {CONFIG_PATH}")

    config = json.loads(
        CONFIG_PATH.read_text(encoding="utf-8")
    )

    project_root = Path(config["project_root"])
    db_path = project_root / "data" / "infinitynikki_photos.db"

    if not db_path.exists():
        raise FileNotFoundError(f"找不到数据库: {db_path}")

    return project_root, db_path


def get_connection():
    _, db_path = load_config()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    return conn


def get_photo_id(cursor, filename):
    cursor.execute("""
        SELECT photo_id
        FROM photos
        WHERE filename=?
    """, (filename,))

    row = cursor.fetchone()

    return row["photo_id"] if row else None


def get_extra_info(cursor, photo_id):
    cursor.execute("""
        SELECT
            outfit_code,
            outfit_description
        FROM outfits
        WHERE photo_id=?
        ORDER BY created_at DESC
    """, (photo_id,))

    outfits = [
        dict(row)
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT
            camera_code,
            description
        FROM camera_params
        WHERE photo_id=?
        ORDER BY created_at DESC
    """, (photo_id,))

    camera_params = [
        dict(row)
        for row in cursor.fetchall()
    ]

    return outfits, camera_params


def make_photo_result(photo, project_root, cursor):
    item = dict(photo)

    relative_path = item.get("path")

    if relative_path:
        absolute_path = (
            project_root / relative_path
        ).resolve()

        item["absolute_path"] = str(
            absolute_path
        )

        try:
            item["file_uri"] = (
                absolute_path.as_uri()
            )
        except ValueError:
            item["file_uri"] = None

    outfits, camera_params = get_extra_info(
        cursor,
        item["photo_id"]
    )

    item["outfits"] = outfits
    item["camera_params"] = camera_params

    return item


def search_photos(args):
    project_root, _ = load_config()
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            p.photo_id,
            p.filename,
            p.path,
            p.shoot_time,
            p.width,
            p.height,
            p.orientation,

            s.photo_type,
            s.portrait_framing,
            s.portrait_view,
            s.scene_category,
            s.game_time,
            s.color_tone,
            s.background

        FROM photos p

        LEFT JOIN photo_semantics s
        ON p.photo_id=s.photo_id

        WHERE 1=1
    """

    params = []

    filters = [
        ("s.photo_type", args.photo_type),
        ("s.portrait_framing", args.framing),
        ("s.portrait_view", args.view),
        ("s.scene_category", args.scene),
        ("s.game_time", args.game_time),
        ("s.color_tone", args.color_tone),
        ("s.background", args.background),
        ("p.orientation", args.orientation)
    ]

    for column, value in filters:
        if value:
            sql += f" AND {column}=?"
            params.append(value)

    sql += """
        ORDER BY p.shoot_time DESC
        LIMIT ?
    """

    params.append(args.limit)

    cursor.execute(sql, params)
    photos = cursor.fetchall()

    results = [
        make_photo_result(
            photo,
            project_root,
            cursor
        )
        for photo in photos
    ]

    conn.close()

    return {
        "count": len(results),
        "results": results
    }


def get_photo_detail(filename):
    project_root, _ = load_config()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.photo_id,
            p.filename,
            p.path,
            p.shoot_time,
            p.width,
            p.height,
            p.orientation,

            s.photo_type,
            s.portrait_framing,
            s.portrait_view,
            s.scene_category,
            s.game_time,
            s.color_tone,
            s.background

        FROM photos p

        LEFT JOIN photo_semantics s
        ON p.photo_id=s.photo_id

        WHERE p.filename=?
    """, (filename,))

    photo = cursor.fetchone()

    if not photo:
        conn.close()

        return {
            "error": "photo_not_found",
            "filename": filename
        }

    result = make_photo_result(
        photo,
        project_root,
        cursor
    )

    conn.close()

    return result


def get_recreate_card(filename):
    detail = get_photo_detail(filename)

    if detail.get("error"):
        return detail

    outfits = detail.get("outfits", [])
    camera_params = detail.get(
        "camera_params",
        []
    )

    outfit = outfits[0] if outfits else {}
    camera = (
        camera_params[0]
        if camera_params
        else {}
    )

    return {
        "filename": detail.get("filename"),
        "absolute_path": detail.get(
            "absolute_path"
        ),
        "file_uri": detail.get("file_uri"),

        "photo": {
            "orientation":
                detail.get("orientation"),
            "photo_type":
                detail.get("photo_type"),
            "portrait_framing":
                detail.get(
                    "portrait_framing"
                ),
            "portrait_view":
                detail.get(
                    "portrait_view"
                ),
            "scene_category":
                detail.get(
                    "scene_category"
                ),
            "game_time":
                detail.get("game_time"),
            "color_tone":
                detail.get("color_tone"),
            "background":
                detail.get("background")
        },

        "outfit": {
            "code":
                outfit.get("outfit_code"),
            "description":
                outfit.get(
                    "outfit_description"
                )
        },

        "camera": {
            "code":
                camera.get("camera_code"),
            "description":
                camera.get("description")
        }
    }


def set_outfit(filename, code, description=None):
    conn = get_connection()
    cursor = conn.cursor()

    photo_id = get_photo_id(
        cursor,
        filename
    )

    if not photo_id:
        conn.close()

        return {
            "error": "photo_not_found",
            "filename": filename
        }

    cursor.execute("""
        SELECT outfit_id
        FROM outfits
        WHERE photo_id=?
        ORDER BY created_at DESC
        LIMIT 1
    """, (photo_id,))

    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE outfits
            SET
                outfit_code=?,
                outfit_description=?
            WHERE outfit_id=?
        """, (
            code,
            description,
            row["outfit_id"]
        ))

        action = "updated"

    else:
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
            code,
            description
        ))

        action = "created"

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "action": action,
        "filename": filename,
        "outfit_code": code,
        "description": description
    }


def set_camera(filename, code, description=None):
    conn = get_connection()
    cursor = conn.cursor()

    photo_id = get_photo_id(
        cursor,
        filename
    )

    if not photo_id:
        conn.close()

        return {
            "error": "photo_not_found",
            "filename": filename
        }

    cursor.execute("""
        SELECT camera_id
        FROM camera_params
        WHERE photo_id=?
        ORDER BY created_at DESC
        LIMIT 1
    """, (photo_id,))

    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE camera_params
            SET
                camera_code=?,
                description=?
            WHERE camera_id=?
        """, (
            code,
            description,
            row["camera_id"]
        ))

        action = "updated"

    else:
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
            code,
            description
        ))

        action = "created"

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "action": action,
        "filename": filename,
        "camera_code": code,
        "description": description
    }


def get_status():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM photos"
    )
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM photos
        WHERE analysis_status='completed'
    """)
    completed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM photos
        WHERE analysis_status='pending'
    """)
    pending = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM photos
        WHERE analysis_status='failed'
    """)
    failed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM photo_semantics
    """)
    semantics = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM outfits
    """)
    outfits = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM camera_params
    """)
    camera_params = cursor.fetchone()[0]

    conn.close()

    return {
        "database": "ok",
        "total_photos": total,
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "semantic_records": semantics,
        "outfit_records": outfits,
        "camera_records": camera_params
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Infinity Nikki Photo Skill"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    subparsers.add_parser(
        "status"
    )

    search = subparsers.add_parser(
        "search"
    )

    search.add_argument(
        "--photo-type",
        choices=["portrait", "scenery"]
    )

    search.add_argument(
        "--framing",
        choices=[
            "close_up",
            "half_body",
            "full_body"
        ]
    )

    search.add_argument(
        "--view",
        choices=[
            "front",
            "back",
            "side"
        ]
    )

    search.add_argument(
        "--scene",
        choices=[
            "architecture",
            "nature",
            "animal",
            "insect",
            "other"
        ]
    )

    search.add_argument(
        "--game-time",
        choices=[
            "day",
            "dusk",
            "night",
            "unknown"
        ]
    )

    search.add_argument(
        "--color-tone",
        choices=["warm", "cool"]
    )

    search.add_argument(
        "--background",
        choices=[
            "white",
            "black",
            "normal"
        ]
    )

    search.add_argument(
        "--orientation",
        choices=[
            "landscape",
            "portrait",
            "square"
        ]
    )

    search.add_argument(
        "--limit",
        type=int,
        default=10
    )

    detail = subparsers.add_parser(
        "detail"
    )

    detail.add_argument(
        "--filename",
        required=True
    )

    recreate = subparsers.add_parser(
        "recreate"
    )

    recreate.add_argument(
        "--filename",
        required=True
    )

    outfit = subparsers.add_parser(
        "set-outfit"
    )

    outfit.add_argument(
        "--filename",
        required=True
    )

    outfit.add_argument(
        "--code",
        required=True
    )

    outfit.add_argument(
        "--description"
    )

    camera = subparsers.add_parser(
        "set-camera"
    )

    camera.add_argument(
        "--filename",
        required=True
    )

    camera.add_argument(
        "--code",
        required=True
    )

    camera.add_argument(
        "--description"
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "search":
            result = search_photos(args)

        elif args.command == "detail":
            result = get_photo_detail(
                args.filename
            )

        elif args.command == "recreate":
            result = get_recreate_card(
                args.filename
            )

        elif args.command == "set-outfit":
            result = set_outfit(
                args.filename,
                args.code,
                args.description
            )

        elif args.command == "set-camera":
            result = set_camera(
                args.filename,
                args.code,
                args.description
            )

        else:
            result = get_status()

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as e:
        print(
            json.dumps(
                {"error": str(e)},
                ensure_ascii=False
            )
        )

        sys.exit(1)


if __name__ == "__main__":
    main()