import json
import base64
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROMPT_FILE = (
    PROJECT_ROOT /
    "references" /
    "photo_analysis_prompt.txt"
)


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5vl:7b"


def load_prompt():
    """加载分析Prompt"""

    with open(
        PROMPT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


def encode_image(image_path):
    """图片转base64"""

    with open(
        image_path,
        "rb"
    ) as f:
        image_data = f.read()

    return base64.b64encode(
        image_data
    ).decode("utf-8")


def parse_vlm_result(text):
    """
    解析JSON输出
    """

    text = text.replace(
        "```json",
        ""
    )

    text = text.replace(
        "```",
        ""
    )

    return json.loads(
        text.strip()
    )


def analyze_image(image_path):
    """
    调用Ollama视觉模型
    """

    prompt = load_prompt()

    image_base64 = encode_image(
        image_path
    )


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
                "num_ctx": 8192
            }
        },
        timeout=300
    )

    print(response.text)

    response.raise_for_status()

    result = response.json()


    content = (
        result["message"]["content"]
    )


    print("\n模型输出:")
    print(content)


    return parse_vlm_result(
        content
    )