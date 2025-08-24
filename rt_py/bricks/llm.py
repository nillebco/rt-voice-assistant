from openai import OpenAI
import tiktoken


def get_client(url=None, api_key=None):
    if not url:
        url = "https://openrouter.ai/api/v1"
    client = OpenAI(
        base_url=url,
        api_key=api_key,
    )
    return client


enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(msgs):
    return sum(
        len(enc.encode((m.get("content") or "") + (m.get("name") or ""))) for m in msgs
    )


def trim_to_budget(history, system_prompt, budget=6000):
    msgs = [{"role": "system", "content": system_prompt}] + history
    while count_tokens(msgs) > budget and len(history) > 2:
        history.pop(0)
        msgs = [{"role": "system", "content": system_prompt}] + history
    return msgs
