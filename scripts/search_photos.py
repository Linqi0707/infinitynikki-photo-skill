import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def search_photos(
    game_time=None,
    background=None,
    photo_type=None,
    framing=None
):

    conn = get_connection()
    cursor = conn.cursor()


    sql = """
        SELECT
            p.filename,
            p.photo_id,
            s.*
        FROM photos p
        JOIN photo_semantics s
        ON p.photo_id=s.photo_id
        WHERE 1=1
    """


    params = []


    if game_time:

        sql += """
        AND s.game_time=?
        """

        params.append(
            game_time
        )


    if background:

        sql += """
        AND s.background=?
        """

        params.append(
            background
        )


    if photo_type:

        sql += """
        AND s.photo_type=?
        """

        params.append(
            photo_type
        )


    if framing:

        sql += """
        AND s.portrait_framing=?
        """

        params.append(
            framing
        )


    cursor.execute(
        sql,
        params
    )


    results = cursor.fetchall()

    conn.close()

    return results



def main():

    results = search_photos(
        game_time="night",
        background="white",
        framing="full_body"
    )


    print(
        f"找到 {len(results)} 张照片"
    )


    for item in results:

        print("-"*40)

        print(
            item["filename"]
        )

        print(
            "类型:",
            item["photo_type"]
        )

        print(
            "时间:",
            item["game_time"]
        )

        print(
            "背景:",
            item["background"]
        )


if __name__ == "__main__":
    main()