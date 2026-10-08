"""
InfinityNikki Photo Skill - Web UI Backend
Flask server that reuses the existing SQLite database and query logic.

Run:  python web/app.py
Open: http://localhost:5000
"""

import sys
import os
import json
import shutil
from pathlib import Path

# --- Project root setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, send_file, jsonify, request, render_template
from src.database import get_connection

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PHOTOS_DIR = PROJECT_ROOT / "data" / "photos"
TRASH_DIR = PROJECT_ROOT / "data" / "trash"
PAGE_SIZE_DEFAULT = 60
PAGE_SIZE_MAX = 200

# Tag dimensions and their DB column mapping
TAG_DIMENSIONS = [
    {
        "key": "photo_type",
        "column": "s.photo_type",
        "label": "照片类型",
        "choices": ["portrait", "scenery"],
        "labels": {"portrait": "人像", "scenery": "景象"},
    },
    {
        "key": "framing",
        "column": "s.portrait_framing",
        "label": "构图",
        "choices": ["close_up", "half_body", "full_body"],
        "labels": {"close_up": "大头照", "half_body": "半身照", "full_body": "全身照"},
    },
    {
        "key": "view",
        "column": "s.portrait_view",
        "label": "视角",
        "choices": ["front", "back", "side"],
        "labels": {"front": "正面", "back": "背面", "side": "侧面"},
    },
    {
        "key": "scene",
        "column": "s.scene_category",
        "label": "场景",
        "choices": ["architecture", "nature", "animal", "insect", "other"],
        "labels": {
            "architecture": "建筑",
            "nature": "自然风景",
            "animal": "动物",
            "insect": "昆虫",
            "other": "其他",
        },
    },
    {
        "key": "game_time",
        "column": "s.game_time",
        "label": "游戏时间",
        "choices": ["day", "dusk", "night", "unknown"],
        "labels": {"day": "白天", "dusk": "黄昏", "night": "夜晚", "unknown": "未知"},
    },
    {
        "key": "color_tone",
        "column": "s.color_tone",
        "label": "色调",
        "choices": ["warm", "cool"],
        "labels": {"warm": "暖色", "cool": "冷色"},
    },
    {
        "key": "background",
        "column": "s.background",
        "label": "背景",
        "choices": ["white", "black", "normal"],
        "labels": {"white": "白色", "black": "黑色", "normal": "普通环境"},
    },
    {
        "key": "orientation",
        "column": "p.orientation",
        "label": "横竖屏",
        "choices": ["landscape", "portrait", "square"],
        "labels": {"landscape": "横屏", "portrait": "竖屏", "square": "方形"},
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_photo_file_path(photo_id):
    """Return the local file path for a given photo_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename FROM photos WHERE photo_id = ?", (photo_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    local_path = PHOTOS_DIR / row["filename"]
    if local_path.exists():
        return local_path
    # Fallback: try the original DB path
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT path FROM photos WHERE photo_id = ?", (photo_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row and Path(row["path"]).exists():
        return Path(row["path"])
    return None


def _get_extra_info(cursor, photo_id):
    """Fetch outfits and camera params for a photo."""
    cursor.execute(
        """
        SELECT outfit_code, outfit_description
        FROM outfits
        WHERE photo_id = ?
        ORDER BY created_at DESC
        """,
        (photo_id,),
    )
    outfits = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """
        SELECT camera_code, description
        FROM camera_params
        WHERE photo_id = ?
        ORDER BY created_at DESC
        """,
        (photo_id,),
    )
    camera_params = [dict(r) for r in cursor.fetchall()]
    return outfits, camera_params


# ---------------------------------------------------------------------------
# Routes - Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Routes - API
# ---------------------------------------------------------------------------
@app.route("/api/tags")
def api_tags():
    """Return all tag dimensions with available values for the filter UI."""
    return jsonify({"dimensions": TAG_DIMENSIONS})


@app.route("/api/photos")
def api_photos():
    """
    Paginated photo list with optional tag filters.

    Query params:
      page (int)        - page number, default 1
      page_size (int)   - items per page, default 60, max 200
      photo_type        - portrait | scenery
      framing           - close_up | half_body | full_body
      view              - front | back | side
      scene             - architecture | nature | animal | insect | other
      game_time         - day | dusk | night | unknown
      color_tone        - warm | cool
      background        - white | black | normal
      orientation       - landscape | portrait | square
    """
    page = max(1, request.args.get("page", 1, type=int))
    page_size = request.args.get("page_size", PAGE_SIZE_DEFAULT, type=int)
    page_size = max(1, min(page_size, PAGE_SIZE_MAX))

    # Build WHERE clauses from query params
    where_clauses = []
    params = []

    for dim in TAG_DIMENSIONS:
        val = request.args.get(dim["key"])
        if val:
            where_clauses.append(f"{dim['column']} = ?")
            params.append(val)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    conn = get_connection()
    cursor = conn.cursor()

    # Count total
    count_sql = f"""
        SELECT COUNT(*)
        FROM photos p
        LEFT JOIN photo_semantics s ON p.photo_id = s.photo_id
        {where_sql}
    """
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    # Fetch page
    offset = (page - 1) * page_size
    data_sql = f"""
        SELECT
            p.photo_id,
            p.filename,
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
        LEFT JOIN photo_semantics s ON p.photo_id = s.photo_id
        {where_sql}
        ORDER BY p.shoot_time DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(data_sql, params + [page_size, offset])
    photos = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify(
        {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "photos": photos,
        }
    )


@app.route("/api/photo/<photo_id>")
def api_photo_detail(photo_id):
    """Full detail for a single photo including semantics, outfits, camera params."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            p.photo_id,
            p.filename,
            p.path,
            p.shoot_time,
            p.suffix_id,
            p.width,
            p.height,
            p.orientation,
            p.sha256,
            p.analysis_status,
            p.created_at,
            s.photo_type,
            s.portrait_framing,
            s.portrait_view,
            s.scene_category,
            s.game_time,
            s.color_tone,
            s.background,
            s.analyzed_at
        FROM photos p
        LEFT JOIN photo_semantics s ON p.photo_id = s.photo_id
        WHERE p.photo_id = ?
        """,
        (photo_id,),
    )
    photo = cursor.fetchone()

    if not photo:
        conn.close()
        return jsonify({"error": "photo_not_found", "photo_id": photo_id}), 404

    result = dict(photo)
    outfits, camera_params = _get_extra_info(cursor, photo_id)
    result["outfits"] = outfits
    result["camera_params"] = camera_params

    conn.close()
    return jsonify(result)


# ---------------------------------------------------------------------------
# Photo edit API
# ---------------------------------------------------------------------------
SEMANTIC_ALLOWED_VALUES = {
    "photo_type": ["portrait", "scenery"],
    "portrait_framing": ["close_up", "half_body", "full_body"],
    "portrait_view": ["front", "back", "side"],
    "scene_category": ["architecture", "nature", "animal", "insect", "other"],
    "game_time": ["day", "dusk", "night", "unknown"],
    "color_tone": ["warm", "cool"],
    "background": ["white", "black", "normal"],
}


@app.route("/api/photo/<photo_id>", methods=["PUT"])
def api_photo_update(photo_id):
    """
    Update a photo's semantic tags, outfit, and camera params.

    Request JSON:
    {
        "semantics": {
            "photo_type": "portrait",
            "portrait_framing": "full_body",
            "portrait_view": "front",
            "scene_category": null,
            "game_time": "night",
            "color_tone": "cool",
            "background": "normal"
        },
        "outfit": {
            "code": "...",
            "description": "..."
        },
        "camera": {
            "code": "...",
            "description": "..."
        }
    }

    - photo_semantics: UPSERT by photo_id
    - outfit: UPDATE latest row if exists, else INSERT
    - camera_params: same as outfit
    - Uses transaction, rollback on error
    - Returns full updated photo detail JSON
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "invalid_json"}), 400

    # --- 1. Check photo exists ---
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT photo_id FROM photos WHERE photo_id = ?", (photo_id,)
    )
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "photo_not_found", "photo_id": photo_id}), 404

    semantics = body.get("semantics", {})
    outfit = body.get("outfit", {})
    camera = body.get("camera", {})

    # --- 2. Validate semantic field values ---
    for field, allowed in SEMANTIC_ALLOWED_VALUES.items():
        val = semantics.get(field, None)
        if val is not None and val != "" and val not in allowed:
            conn.close()
            return (
                jsonify(
                    {
                        "error": "validation_error",
                        "field": field,
                        "value": val,
                        "allowed": allowed,
                    }
                ),
                400,
            )
        # Treat empty string as None
        if val == "":
            val = None
        semantics[field] = val

    try:
        # --- 3. UPSERT photo_semantics ---
        cursor.execute(
            """
            INSERT INTO photo_semantics (
                photo_id, photo_type, portrait_framing,
                portrait_view, scene_category, game_time,
                color_tone, background, analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(photo_id) DO UPDATE SET
                photo_type = excluded.photo_type,
                portrait_framing = excluded.portrait_framing,
                portrait_view = excluded.portrait_view,
                scene_category = excluded.scene_category,
                game_time = excluded.game_time,
                color_tone = excluded.color_tone,
                background = excluded.background,
                analyzed_at = CURRENT_TIMESTAMP
            """,
            (
                photo_id,
                semantics.get("photo_type"),
                semantics.get("portrait_framing"),
                semantics.get("portrait_view"),
                semantics.get("scene_category"),
                semantics.get("game_time"),
                semantics.get("color_tone"),
                semantics.get("background"),
            ),
        )

        # --- 4. Update or insert outfit ---
        outfit_code = outfit.get("code", "").strip()
        outfit_desc = outfit.get("description", "").strip()
        if outfit_code or outfit_desc:
            cursor.execute(
                """
                SELECT outfit_id FROM outfits
                WHERE photo_id = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (photo_id,),
            )
            existing_outfit = cursor.fetchone()
            if existing_outfit:
                cursor.execute(
                    """
                    UPDATE outfits
                    SET outfit_code = ?, outfit_description = ?
                    WHERE outfit_id = ?
                    """,
                    (outfit_code, outfit_desc, existing_outfit["outfit_id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO outfits (photo_id, outfit_code, outfit_description)
                    VALUES (?, ?, ?)
                    """,
                    (photo_id, outfit_code, outfit_desc),
                )

        # --- 5. Update or insert camera params ---
        camera_code = camera.get("code", "").strip()
        camera_desc = camera.get("description", "").strip()
        if camera_code or camera_desc:
            cursor.execute(
                """
                SELECT camera_id FROM camera_params
                WHERE photo_id = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (photo_id,),
            )
            existing_camera = cursor.fetchone()
            if existing_camera:
                cursor.execute(
                    """
                    UPDATE camera_params
                    SET camera_code = ?, description = ?
                    WHERE camera_id = ?
                    """,
                    (camera_code, camera_desc, existing_camera["camera_id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO camera_params (photo_id, camera_code, description)
                    VALUES (?, ?, ?)
                    """,
                    (photo_id, camera_code, camera_desc),
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return (
            jsonify({"error": "database_error", "detail": str(e)}),
            500,
        )

    # --- 6. Return full updated detail ---
    cursor.execute(
        """
        SELECT
            p.photo_id,
            p.filename,
            p.path,
            p.shoot_time,
            p.suffix_id,
            p.width,
            p.height,
            p.orientation,
            p.sha256,
            p.analysis_status,
            p.created_at,
            s.photo_type,
            s.portrait_framing,
            s.portrait_view,
            s.scene_category,
            s.game_time,
            s.color_tone,
            s.background,
            s.analyzed_at
        FROM photos p
        LEFT JOIN photo_semantics s ON p.photo_id = s.photo_id
        WHERE p.photo_id = ?
        """,
        (photo_id,),
    )
    photo = cursor.fetchone()
    result = dict(photo)
    outfits, camera_params = _get_extra_info(cursor, photo_id)
    result["outfits"] = outfits
    result["camera_params"] = camera_params

    conn.close()
    return jsonify(result)


@app.route("/api/search")
def api_search():
    """
    Keyword search by filename.

    Query params:
      q (str)       - search keyword (matches filename)
      page (int)    - page number
      page_size     - items per page
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"total": 0, "photos": [], "page": 1, "total_pages": 0})

    page = max(1, request.args.get("page", 1, type=int))
    page_size = request.args.get("page_size", PAGE_SIZE_DEFAULT, type=int)
    page_size = max(1, min(page_size, PAGE_SIZE_MAX))

    conn = get_connection()
    cursor = conn.cursor()

    like_pattern = f"%{q}%"

    count_sql = """
        SELECT COUNT(*)
        FROM photos p
        LEFT JOIN photo_semantics s ON p.photo_id = s.photo_id
        WHERE p.filename LIKE ?
    """
    cursor.execute(count_sql, (like_pattern,))
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    data_sql = """
        SELECT
            p.photo_id,
            p.filename,
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
        LEFT JOIN photo_semantics s ON p.photo_id = s.photo_id
        WHERE p.filename LIKE ?
        ORDER BY p.shoot_time DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(data_sql, (like_pattern, page_size, offset))
    photos = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify(
        {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "photos": photos,
            "query": q,
        }
    )


@app.route("/api/photo_file/<photo_id>")
def api_photo_file(photo_id):
    """Serve the actual JPEG image file for a photo."""
    file_path = _get_photo_file_path(photo_id)
    if not file_path or not file_path.exists():
        return jsonify({"error": "file_not_found", "photo_id": photo_id}), 404
    return send_file(str(file_path), mimetype="image/jpeg")


@app.route("/api/stats")
def api_stats():
    """Database statistics summary."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM photos")
    total_photos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM photo_semantics")
    total_semantics = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM outfits")
    total_outfits = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM camera_params")
    total_camera = cursor.fetchone()[0]

    # Orientation breakdown
    cursor.execute(
        "SELECT orientation, COUNT(*) FROM photos GROUP BY orientation"
    )
    orientation_breakdown = {r[0]: r[1] for r in cursor.fetchall()}

    conn.close()

    return jsonify(
        {
            "total_photos": total_photos,
            "total_semantics": total_semantics,
            "total_outfits": total_outfits,
            "total_camera_params": total_camera,
            "orientation_breakdown": orientation_breakdown,
        }
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("InfinityNikki Photo Skill - Web UI")
    print(f"Database: {PROJECT_ROOT / 'data' / 'infinitynikki_photos.db'}")
    print(f"Photos dir: {PHOTOS_DIR}")
    print(f"Photos found: {len(list(PHOTOS_DIR.glob('*.jpeg')))} files")
    print("=" * 50)
    print("Server starting at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=True)
