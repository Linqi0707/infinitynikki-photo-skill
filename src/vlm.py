import json
import base64
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = PROJECT_ROOT / "references" / "photo_analysis_prompt.txt"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5vl:7b"

MAX_IMAGE_SIZE = 1024
JPEG_QUALITY = 85


def load_prompt():
    return PROMPT_FILE.read_text(encoding="utf-8")


def encode_image(image_path):
    """缩放图片后转Base64，不修改原图"""

    with Image.open(image_path) as img:
        img = img.convert("RGB")

        width, height = img.size
        scale = min(
            MAX_IMAGE_SIZE / max(width, height),
            1
        )

        if scale < 1:
            img = img.resize(
                (
                    int(width * scale),
                    int(height * scale)
                ),
                Image.Resampling.LANCZOS
            )

        buffer = BytesIO()

        img.save(
            buffer,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True
        )

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


def parse_vlm_result(text):
    text = text.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    return json.loads(text)


def analyze_image(image_path):
    prompt = load_prompt()
    image_base64 = encode_image(image_path)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [
                        image_base64
                    ]
                }
            ],
            "stream": False,
            "options": {
                "num_ctx": 8192,
                "temperature": 0
            }
        },
        timeout=300
    )

    if not response.ok:
        print(response.text)

    response.raise_for_status()

    content = response.json()[
        "message"
    ][
        "content"
    ]

    print("\n模型输出:")
    print(content)

    return parse_vlm_result(content)