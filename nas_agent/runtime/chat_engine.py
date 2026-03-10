# runtime/chat_engine.py

from utils.deps import ensure_package
from utils.helpers import safe_get
from config.settings import MODEL_NAME, SHOW_THINKING, THINK_LEVEL

ensure_package("ollama")
from ollama import chat, list as ollama_list


def check_model_exists() -> bool:
    try:
        resp = ollama_list()
        models = safe_get(resp, "models", [])
        names = []

        for m in models:
            name = safe_get(m, "model", "") or safe_get(m, "name", "")
            if name:
                names.append(name)

        return MODEL_NAME in names
    except Exception as e:
        print(f"⚠️ 检查模型时出错: {e}")
        return False


def extract_content_from_chunk(chunk):
    msg = safe_get(chunk, "message", {}) or {}
    thinking = safe_get(msg, "thinking", "") or ""
    content = safe_get(msg, "content", "") or ""
    return str(thinking), str(content)


def stream_chat(messages) -> str:
    stream = chat(
        model=MODEL_NAME,
        messages=messages,
        stream=True,
        think=THINK_LEVEL,
        options={
            "temperature": 0.6,
            "top_p": 0.9,
            "num_predict": 512,
        }
    )

    full_reply = ""
    in_fallback_think_block = False

    print("\n🤖 本地 Agent: ", end="", flush=True)

    for chunk in stream:
        thinking, content = extract_content_from_chunk(chunk)

        if SHOW_THINKING and thinking:
            print(thinking, end="", flush=True)

        if content:
            text = content

            if "<think>" in text:
                in_fallback_think_block = True
                text = text.replace("<think>", "")

            if "</think>" in text:
                text = text.replace("</think>", "")
                in_fallback_think_block = False
                continue

            if in_fallback_think_block:
                if SHOW_THINKING and text:
                    print(text, end="", flush=True)
            else:
                if text:
                    print(text, end="", flush=True)
                    full_reply += text

    print()
    return full_reply.strip()