"""
app.py
------
Flask backend for the web chatbot.

Flow for every message:
  1. Try the local NLP engine (NLTK preprocessing + TF-IDF/cosine
     similarity intent matching + skills like math/conversions/date-time).
  2. If that engine isn't confident, fall back to the Claude API for a
     general-purpose answer.
  3. Return JSON with the reply + which layer answered it (shown in the UI
     as a small badge, useful for demonstrating the NLP layer to a grader).

Run with:
    python app.py
Then open http://localhost:5000 in a browser.
"""

import os
from flask import Flask, request, jsonify, render_template

from chatbot_engine import ChatBot
from ai_fallback import ask_ai, is_configured

app = Flask(__name__)

INTENTS_PATH = os.path.join(os.path.dirname(__file__), "intents.json")
bot = ChatBot(INTENTS_PATH, confidence_threshold=0.35)

# Simple in-memory per-session history (keyed by a session id sent from the
# browser). Fine for a demo/assignment; not meant for multi-user production.
_HISTORY = {}
_MAX_HISTORY_TURNS = 6  # keep last N user/assistant turn-pairs sent to the AI


@app.route("/")
def index():
    return render_template("index.html", ai_configured=is_configured())


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or "default"

    if not user_message:
        return jsonify({"reply": "Please type something!", "source": "system"})

    # Layer 1: local NLP engine (NLTK + TF-IDF + skills)
    reply, tag, score = bot.get_response(user_message)

    if reply:
        source = "skill" if tag in ("math", "convert", "datetime", "facts") else "nlp"
        return jsonify({
            "reply": reply,
            "source": source,
            "matched": tag,
            "confidence": round(score, 3),
        })

    # Layer 2: AI fallback for anything the local engine can't confidently answer
    history = _HISTORY.get(session_id, [])
    ai_reply = ask_ai(user_message, history=history)

    if ai_reply.startswith("[AI ERROR]"):
        return jsonify({
            "reply": (
                "I couldn't find a confident local answer, and the AI fallback "
                "isn't available right now (" + ai_reply.replace("[AI ERROR] ", "") + "). "
                "Try rephrasing, or ask about math, conversions, dates, or common topics."
            ),
            "source": "error",
            "matched": None,
            "confidence": round(score, 3),
        })

    # update history for this session
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_reply},
    ]
    _HISTORY[session_id] = history[-(_MAX_HISTORY_TURNS * 2):]

    return jsonify({
        "reply": ai_reply,
        "source": "ai",
        "matched": None,
        "confidence": round(score, 3),
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or "default"
    _HISTORY.pop(session_id, None)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 60)
    print(" NLP + AI Web Chatbot")
    print(f" Local NLP backend: {bot.backend_info()}")
    print(f" AI fallback configured: {is_configured()}")
    if not is_configured():
        print(" (Set ANTHROPIC_API_KEY env variable to enable AI fallback)")
    print(" Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(debug=True, port=5000)
