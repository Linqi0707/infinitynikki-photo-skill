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

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_condition(text):
    """自然语言解析为查询条件"""

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

    result = response.json()

    content = result["message"]["content"]

    content = content.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    return json.loads(content)


def search_photos(condition):
    """根据条件查询照片"""

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            p.filename,
            p.photo_id
        FROM photos p
        JOIN photo_semantics s
        ON p.photo_id=s.photo_id
        WHERE 1=1
    """

    params = []

    mapping = {
        "game_time": "game_time",
        "background": "background",
        "photo_type": "photo_type",
        "portrait_framing": "portrait_framing",
        "color_tone": "color_tone"
    }

    for key, column in mapping.items():

        if condition.get(key):

            sql += f"""
            AND s.{column}=?
            """

            params.append(
                condition[key]
            )

    cursor.execute(
        sql,
        params
    )

    results = cursor.fetchall()

    conn.close()

    return results


def main():

    question = input(
        "请输入搜索需求: "
    ).strip()


    condition = parse_condition(
        question
    )


    print("\n解析条件:")
    print(
        json.dumps(
            condition,
            ensure_ascii=False,
            indent=2
        )
    )


    results = search_photos(
        condition
    )


    print(
        f"\n找到 {len(results)} 张照片:"
    )


    for item in results:

        print(
            item["filename"]
        )


if __name__ == "__main__":
    main()