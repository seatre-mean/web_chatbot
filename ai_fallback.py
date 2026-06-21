"""
ai_fallback.py
--------------
Fallback answering layer using the Anthropic API (Claude), used ONLY when
the local NLTK/TF-IDF engine (chatbot_engine.py) can't confidently answer
a query. This is what lets the bot handle truly open-ended questions
("explain quantum entanglement", "write me a haiku about rain", etc.)
that a small hand-built knowledge base never could.

Setup required:
    1. Get an API key from https://console.anthropic.com/
    2. Set it as an environment variable before running the server:
         Windows (cmd):   set ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
         Windows (PS):    $env:ANTHROPIC_API_KEY="sk-ant-xxxxxxxx"
         Mac/Linux:       export ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
       OR just edit API_KEY below directly (not recommended for shared code).

If no key is configured, this module fails gracefully and the chatbot
will say so rather than crashing.
"""

import os
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # or hardcode your key here as a string
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a helpful, friendly chatbot embedded in a web page. "
    "Keep answers concise (2-5 sentences) and conversational unless the "
    "user clearly asks for something longer (like a list, code, or a story)."
)


def is_configured() -> bool:
    return bool(API_KEY)


def ask_ai(user_message: str, history=None):
    """
    Sends user_message (plus optional prior conversation `history`, a list
    of {"role": "user"/"assistant", "content": str}) to the Claude API.

    Returns the reply text, or an error message string starting with
    "[AI ERROR]" if something went wrong (caller can detect this prefix).
    """
    if not API_KEY:
        return ("[AI ERROR] No ANTHROPIC_API_KEY configured. Set the "
                "ANTHROPIC_API_KEY environment variable to enable AI fallback "
                "for open-ended questions.")

    messages = list(history) if history else []
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL,
        "max_tokens": 500,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parts = data.get("content", [])
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            return text.strip() or "[AI ERROR] Empty response from API."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(body)
            msg = err_json.get("error", {}).get("message", body)
        except Exception:
            msg = body
        return f"[AI ERROR] API request failed ({e.code}): {msg}"
    except urllib.error.URLError as e:
        return f"[AI ERROR] Could not reach the API (network issue): {e.reason}"
    except Exception as e:
        return f"[AI ERROR] Unexpected error: {e}"
