"""Minh hoạ FUNCTION CALLING với xKiro Gateway (OpenAI-compatible).

Sử dụng endpoint của xKiro (https://api.xkiro.com/v1) với model Mistral Large.
Tool `get_weather` được định nghĩa JSON Schema theo chuẩn OpenAI và app tự thực thi.

Cách chạy:
    python weather_function_calling_xkiro.py
"""

import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Nạp file .env từ thư mục gốc hoặc hiện tại, override các biến môi trường cũ nếu cần
load_dotenv(override=False)

BASE_URL = os.getenv("XKIRO_BASE_URL", "https://api.xkiro.com/v1")
API_KEY = os.getenv("XKIRO_API_KEY") or os.getenv("OPENAI_API_KEY", "sk-xt-b27b5b505fcbb0ed34801aa25378b407dae085e8fd828dc6")
# Nếu biến hệ thống là etfbit, force sang xkiro
if "xkiro" not in BASE_URL:
    BASE_URL = "https://api.xkiro.com/v1"
if not API_KEY.startswith("sk-xt-"):
    API_KEY = "sk-xt-b27b5b505fcbb0ed34801aa25378b407dae085e8fd828dc6"

MODEL = os.getenv("XKIRO_MODEL", "mistralai/mistral-large-2512")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
)

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế."
)

# 1. Định nghĩa Tool theo chuẩn OpenAI JSON Schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thông tin thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Tên thành phố (ví dụ: Hanoi, Danang, Haiphong)"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 2. Hàm thực thi (App tự chạy, Model chỉ quyết định gọi)
def get_weather(city: str) -> str:
    mock_db = {
        "hanoi": {"temp": "28°C", "condition": "Mưa rào rải rác", "humidity": "85%"},
        "danang": {"temp": "31°C", "condition": "Nắng nhiều mây", "humidity": "75%"},
        "haiphong": {"temp": "27°C", "condition": "Mưa to kèm giông", "humidity": "90%"},
    }
    key = city.lower().replace(" ", "").replace("hànội", "hanoi").replace("đànẵng", "danang").replace("hảiphòng", "haiphong")
    data = mock_db.get(key, {"temp": "29°C", "condition": "Có mây", "humidity": "80%"})
    return json.dumps({"city": city, **data}, ensure_ascii=False)

def main():
    print(f"📡 Đang kết nối tới xKiro: {BASE_URL}")
    print(f"🤖 Model: {MODEL}\n")

    user_query = "Thời tiết hôm nay ở Hà Nội và Đà Nẵng thế nào? Tôi có nên mang theo ô không?"
    print(f"👤 User: {user_query}\n")

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_query}
    ]

    # Bước 1: Gửi prompt + danh sách tools tới model
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message
    messages.append(msg)

    # Bước 2: Kiểm tra nếu model yêu cầu gọi tool
    if msg.tool_calls:
        print("⚙️  Model đã yêu cầu gọi Function(s):")
        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"  👉 Calling {func_name}({args})")

            if func_name == "get_weather":
                tool_result = get_weather(**args)
            else:
                tool_result = json.dumps({"error": "Unknown tool"})

            # Bước 3: Đưa kết quả thực thi trở lại cho model
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        print("\n⏳ Đang gửi kết quả tool để model tổng hợp câu trả lời...")
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        print("\n🤖 Trợ lý:")
        print(final_response.choices[0].message.content)
    else:
        print("\n🤖 Trợ lý (không cần gọi tool):")
        print(msg.content)

if __name__ == "__main__":
    main()
