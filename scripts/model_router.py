"""
model_router.py — Nexora AI's model routing layer (Module 5: Model Routing & Cost Optimization).

Strategy:
- Groq is the primary route: fast, cheap, great for quick reasoning
  (deciding tasks, diagnosing CI failures).
- Ollama (local) is the fallback: used automatically if Groq is
  unreachable, rate-limited, or if we want a fully offline demo.

This lets Hermes "think" using a real LLM instead of hardcoded strings,
and shows a genuine multi-model routing strategy rather than a single
hardcoded API call.
"""
import json
import requests
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "model_router_config.json"


def _load_config():
    return json.loads(CONFIG_PATH.read_text())


def ask_groq(prompt: str, config: dict) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['groq_api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config["groq_model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def ask_ollama(prompt: str, config: dict) -> str:
    body = {
        "model": config["ollama_model"],
        "prompt": prompt,
        "stream": False,
    }
    resp = requests.post(config["ollama_url"], json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()["response"].strip()


def route(prompt: str) -> dict:
    """
    Tries Groq first (fast + cheap). Falls back to local Ollama if Groq
    fails for any reason (no internet, rate limit, bad key, etc).
    Returns which model actually answered, for transparency in logs.
    """
    config = _load_config()

    try:
        answer = ask_groq(prompt, config)
        return {"model_used": "groq", "answer": answer}
    except Exception as groq_error:
        print(f"[model_router] Groq failed ({groq_error}), falling back to Ollama...")
        try:
            answer = ask_ollama(prompt, config)
            return {"model_used": "ollama (fallback)", "answer": answer}
        except Exception as ollama_error:
            return {"model_used": "none", "answer": f"Both routes failed: {ollama_error}"}


if __name__ == "__main__":
    result = route("In one short sentence, what does a CI pipeline do?")
    print(f"Answered by: {result['model_used']}")
    print(result["answer"])