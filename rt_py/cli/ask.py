# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openai",
#     "tiktoken",
# ]
# ///

import os
import sys
import signal
from dotenv import load_dotenv
from rt_py.bricks.llm import trim_to_budget, get_client

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "openai/gpt-4o")
URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

if __name__ == "__main__":
    running = True
    client = get_client(api_key=API_KEY, url=URL)

    def handle_sigint(sig, frame):
        global running
        running = False


    signal.signal(signal.SIGINT, handle_sigint)

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        system = "You are a concise, helpful assistant."
        history = []
        history.append({"role": "user", "content": text})
        messages = trim_to_budget(history, system, budget=6000)
        resp = client.chat.completions.create(model=MODEL, messages=messages)
        answer = resp.choices[0].message.content
        history.append({"role": "assistant", "content": answer})
        print(answer)
        exit(0)

    print("Press Ctrl+D or enter an empty line to exit.")
    while running:
        text = sys.stdin.readline().strip()
        if not text:
            break

        system = "You are a concise, helpful assistant."
        history = []
        history.append({"role": "user", "content": text})

        messages = trim_to_budget(history, system, budget=6000)
        resp = client.chat.completions.create(model=MODEL, messages=messages)
        answer = resp.choices[0].message.content
        history.append({"role": "assistant", "content": answer})
