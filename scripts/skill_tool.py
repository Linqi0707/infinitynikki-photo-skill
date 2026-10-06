import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def get_extra_info(cursor, photo_id):
    cursor.execute("""
        SELECT outfit_code, outfit_description
        FROM outfits
        WHERE photo_id=?
        ORDER BY created_at DESC
    """, (photo_id,))
    outfits = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT camera_code, description
        FROM camera_params
        WHERE photo_id=?
        ORDER BY created_at DESC
    """, (photo_id,))
    camera_params = [dict(row) for row in cursor.fetchall()]

    return outfits, camera_params


def search_photos(args):
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

    filters = {
        "photo_type": ("s.photo_type", args.photo_type),
        "framing": ("s.portrait_framing", args.framing),
        "view": ("s.portrait_view", args.view),
        "scene": ("s.scene_category", args.scene),
        "game_time": ("s.game_time", args.game_time),
        "color_tone": ("s.color_tone", args.color_tone),
        "background": ("s.background", args.background),
        "orientation": ("p.orientation", args.orientation)
    }

    for _, (column, value) in filters.items():
        if value:
            sql += f" AND {column}=?"
            params.append(value)

    sql += " ORDER BY p.shoot_time DESC LIMIT ?"
    params.append(args.limit)

    cursor.execute(sql, params)
    photos = cursor.fetchall()

    results = []

    for photo in photos:
        item = dict(photo)
        outfits, camera_params = get_extra_info(
            cursor,
            photo["photo_id"]
        )

        item["outfits"] = outfits
        item["camera_params"] = camera_params
        results.append(item)

    conn.close()

    return {
        "count": len(results),
        "results": results
    }


def get_photo_detail(filename):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.*,
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

    result = dict(photo)

    outfits, camera_params = get_extra_info(
        cursor,
        photo["photo_id"]
    )

    result["outfits"] = outfits
    result["camera_params"] = camera_params

    conn.close()

    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="Infinity Nikki Photo Skill Tool"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    search = subparsers.add_parser(
        "search",
        help="按标签搜索照片"
    )

    search.add_argument(
        "--photo-type",
        choices=["portrait", "scenery"]
    )

    search.add_argument(
        "--framing",
        choices=["close_up", "half_body", "full_body"]
    )

    search.add_argument(
        "--view",
        choices=["front", "back", "side"]
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
        choices=["day", "dusk", "night", "unknown"]
    )

    search.add_argument(
        "--color-tone",
        choices=["warm", "cool"]
    )

    search.add_argument(
        "--background",
        choices=["white", "black", "normal"]
    )

    search.add_argument(
        "--orientation",
        choices=["landscape", "portrait", "square"]
    )

    search.add_argument(
        "--limit",
        type=int,
        default=20
    )

    detail = subparsers.add_parser(
        "detail",
        help="查询单张照片完整信息"
    )

    detail.add_argument(
        "--filename",
        required=True
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "search":
        result = search_photos(args)
    else:
        result = get_photo_detail(args.filename)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()