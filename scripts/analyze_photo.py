import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.semantic import (
    get_pending_photos,
    save_photo_semantics,
    update_analysis_status
)
from src.vlm import analyze_image


BATCH_SIZE = 10


def analyze_batch():
    photos = get_pending_photos(BATCH_SIZE)

    if not photos:
        return 0

    print(f"本批待分析照片数量: {len(photos)}")

    for photo in photos:
        photo_id = photo["photo_id"]
        image_path = Path(photo["path"])

        print(f"\n分析: {photo['filename']}")

        try:
            result = analyze_image(image_path)

            save_photo_semantics(
                photo_id,
                result
            )

            update_analysis_status(
                photo_id,
                "completed"
            )

            print(f"完成: {photo_id}")

        except Exception as e:
            print(f"失败: {photo_id}")
            print(e)

            update_analysis_status(
                photo_id,
                "failed"
            )

    return len(photos)


def main():
    total = 0

    while True:
        count = analyze_batch()

        if count == 0:
            break

        total += count
        print(f"\n累计处理: {total} 张")

    print("\n全部分析任务完成")


if __name__ == "__main__":
    main()