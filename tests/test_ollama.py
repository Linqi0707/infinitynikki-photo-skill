import requests


response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen2.5:7b",
        "messages": [
            {
                "role": "user",
                "content": "你好，请输出JSON：{\"test\":\"ok\"}"
            }
        ],
        "stream": False
    },
    timeout=120
)


print(response.json()["message"]["content"])