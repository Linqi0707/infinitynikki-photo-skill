import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b"


def load_prompt():
    path = PROJECT_ROOT / "references" / "search_prompt.txt"
    return path.read_text(encoding="utf-8")


def parse_condition(text):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": load_prompt()
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    response.raise_for_status()

    content = response.json()["message"]["content"]

    content = content.replace(
        "```json", ""
    ).replace(
        "```", ""
    ).strip()

    return json.loads(content)


def search_photo_detail(condition):
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
            s.background,

            o.outfit_code,
            o.outfit_description,

            c.camera_code,
            c.description AS camera_description

        FROM photos p

        LEFT JOIN photo_semantics s
        ON p.photo_id = s.photo_id

        LEFT JOIN outfits o
        ON p.photo_id = o.photo_id

        LEFT JOIN camera_params c
        ON p.photo_id = c.photo_id

        WHERE 1=1
    """

    params = []

    semantic_mapping = {
        "photo_type": "s.photo_type",
        "portrait_framing": "s.portrait_framing",
        "portrait_view": "s.portrait_view",
        "scene_category": "s.scene_category",
        "game_time": "s.game_time",
        "color_tone": "s.color_tone",
        "background": "s.background"
    }

    for key, column in semantic_mapping.items():
        if condition.get(key):
            sql += f" AND {column} = ?"
            params.append(condition[key])

    if condition.get("orientation"):
        sql += " AND p.orientation = ?"
        params.append(condition["orientation"])

    sql += " ORDER BY p.shoot_time DESC"

    cursor.execute(sql, params)

    results = cursor.fetchall()
    conn.close()

    return results


def main():
    question = input("请输入搜索需求: ").strip()

    if not question:
        print("搜索内容不能为空")
        return

    try:
        condition = parse_condition(question)
    except Exception as e:
        print(f"查询条件解析失败: {e}")
        return

    print("\n解析条件:")
    print(
        json.dumps(
            condition,
            ensure_ascii=False,
            indent=2
        )
    )

    results = search_photo_detail(condition)

    print(f"\n找到 {len(results)} 张照片")

    for item in results:
        print("-" * 60)
        print(f"照片: {item['filename']}")
        print(f"路径: {item['path']}")
        print(f"方向: {item['orientation']}")
        print(f"类型: {item['photo_type']}")
        print(f"构图: {item['portrait_framing']}")
        print(f"视角: {item['portrait_view']}")
        print(f"场景: {item['scene_category']}")
        print(f"游戏时间: {item['game_time']}")
        print(f"色调: {item['color_tone']}")
        print(f"背景: {item['background']}")
        print(f"搭配码: {item['outfit_code'] or '未录入'}")
        print(f"摄影参数: {item['camera_code'] or '未录入'}")


if __name__ == "__main__":
    main()