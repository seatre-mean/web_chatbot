# Dual-Engine Web Chatbot (NLTK + TF-IDF + AI Fallback)

A browser-based chatbot with **two answering layers**:

1. **Local NLP engine** (instant, no internet/API needed): NLTK
   preprocessing (tokenize → remove stopwords → lemmatize) + TF-IDF /
   cosine similarity intent matching, plus a "skills" layer for math,
   unit conversions, date/time, and offline facts. This is the layer that
   demonstrates classic NLP techniques.
2. **AI fallback** (Claude API): for anything open-ended the local engine
   can't confidently answer, the question is sent to Claude, which can
   genuinely answer almost anything.

Every bot reply in the UI is tagged with a small badge — **⚡ instant**
(local NLP/skills) or **🧠 ai** (API fallback) — so you can see which
engine answered, which is useful both for demoing the NLP work and for
debugging.

> **Important, honest caveat:** no chatbot — including this one — can
> truly "answer every question on the planet" or be "fully trained" on
> everything. The local layer is bounded by what's in `intents.json` /
> `skills.py`. The AI layer is very capable but can still be wrong,
> outdated, or refuse certain requests. This setup gets you as close to
> "answers almost anything" as is realistically possible while still
> genuinely demonstrating NLTK/NLP techniques for your assignment.

## Project structure

```
web_chatbot/
├── app.py               # Flask server — routes, ties engine + AI fallback together
├── chatbot_engine.py     # NLTK + TF-IDF/cosine-similarity intent matching
├── skills.py             # Computed answers: math, conversions, date/time, facts
├── nlp_utils.py          # NLTK preprocessing pipeline (+ pure-Python fallback)
├── ai_fallback.py        # Calls the Anthropic (Claude) API for open-ended questions
├── intents.json          # Knowledge base of conversational patterns -> responses
├── requirements.txt
├── templates/
│   └── index.html        # Chat page
└── static/
    ├── style.css          # Dual-engine visual design
    └── chat.js             # Frontend chat logic (fetch calls to /api/chat)
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download NLTK data (one-time)

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

If this isn't available (no internet), `nlp_utils.py` automatically falls
back to a lightweight built-in tokenizer — the app still runs.

### 3. (Optional but recommended) Set up the AI fallback

Without this step, the local NLP engine still works fully — math, unit
conversions, dates, facts, and small talk all answer instantly. But
anything outside that knowledge base will show a friendly "AI fallback
not configured" message instead of a real answer.

To enable it:

1. Go to **https://console.anthropic.com/** and create an API key.
   (This is different from a normal claude.ai login — it's a developer
   account with its own billing.)
2. Set it as an environment variable before running the server:

   **Windows (Command Prompt):**
   ```
   set ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
   **Windows (PowerShell):**
   ```
   $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```
   **Mac/Linux:**
   ```
   export ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

   Note: this only lasts for that terminal session. Set it again each
   time you open a new terminal, or add it to your system's permanent
   environment variables.

## Run it

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

The terminal will print whether NLTK loaded correctly and whether the AI
fallback is configured:

```
============================================================
 NLP + AI Web Chatbot
 Local NLP backend: NLTK (full pipeline)
 AI fallback configured: True
 Open http://localhost:5000 in your browser
============================================================
```

## What it can answer

| Layer | Example | Badge |
|---|---|---|
| Skill: math | "what is 12 * 7" | ⚡ instant |
| Skill: conversion | "convert 5 km to miles" | ⚡ instant |
| Skill: date/time | "what time is it" | ⚡ instant |
| Skill: facts | "capital of japan" | ⚡ instant |
| Intent: small talk | "hi", "how are you", "tell me a joke" | ⚡ instant |
| AI fallback | "explain how vaccines work", "write a haiku about rain" | 🧠 ai |

## How the routing decision works (`app.py`)

```python
reply, tag, score = bot.get_response(user_message)   # try local NLP first
if reply:
    # answered locally — instant, no API call, no cost
    return jsonify({"reply": reply, "source": "skill"/"nlp", ...})
else:
    # local engine wasn't confident — ask the AI
    ai_reply = ask_ai(user_message, history=...)
    return jsonify({"reply": ai_reply, "source": "ai", ...})
```

This means simple/common questions never touch the API (free, instant,
demonstrates the NLP work), and only genuinely open-ended questions cost
an API call.

## Extending it

- **Add more local knowledge:** edit `intents.json` (conversation topics)
  or `skills.py` (`_FACTS` dict, or a new skill function) — no AI call
  needed for things you add here, and it stays free/instant.
- **Tune when it falls back to AI:** adjust `confidence_threshold` in
  `chatbot_engine.py`'s `ChatBot(...)` — lower it to lean more on local
  matching, raise it to lean more on the AI.
- **Change the AI's personality/length:** edit `SYSTEM_PROMPT` in
  `ai_fallback.py`.
- **Deploy it properly:** the Flask dev server (`app.run(debug=True)`)
  is fine for a demo but isn't meant for production. For real deployment,
  use a WSGI server like `gunicorn` and turn off debug mode.

## Troubleshooting

- **"AI fallback not configured" badge/message** → you haven't set
  `ANTHROPIC_API_KEY` in this terminal session (see step 3 above).
- **"Could not reach the API"** → check your internet connection, or that
  your API key is valid and has available credits.
- **NLTK download fails** → the app still works using a fallback
  tokenizer; less accurate but functional. Check your internet connection
  and try the download command again.
- **Page loads but styling looks broken** → make sure the `static/`
  folder (containing `style.css` and `chat.js`) is in the same directory
  as `app.py`, not moved elsewhere.
