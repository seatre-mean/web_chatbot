"""
chatbot_engine.py
------------------
Core NLP matching engine for the chatbot — the part of this project that
demonstrates classic NLP techniques (NLTK preprocessing + TF-IDF/cosine
similarity retrieval), independent of any external AI API.

Two layers of answering, tried in order:

  1. SKILLS (skills.py) — handles queries that need a computed answer:
     math expressions, unit conversions, date/time, quick facts.

  2. INTENT MATCHING (this file) — classic retrieval-based NLP approach:
       a. Load intents.json — each intent has a tag, example "patterns",
          and candidate "responses".
       b. Preprocess every pattern with the NLTK pipeline (nlp_utils.preprocess).
       c. Vectorize all patterns with TF-IDF.
       d. At query time, vectorize the user's message the same way and
          compute cosine similarity against every known pattern.
       e. If the best match clears a confidence threshold (and shares
          enough overlapping words), return a random response from that
          intent. Otherwise, report low confidence so the caller can
          decide to fall back to a more general system (e.g. an AI API).
"""

import json
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nlp_utils import preprocess, using_nltk
from skills import try_skills


class ChatBot:
    def __init__(self, intents_path: str, confidence_threshold: float = 0.35):
        self.confidence_threshold = confidence_threshold
        self.intents = self._load_intents(intents_path)

        self.pattern_texts = []
        self.pattern_tags = []
        self.tag_to_responses = {}

        for intent in self.intents:
            tag = intent["tag"]
            self.tag_to_responses[tag] = intent["responses"]
            for pattern in intent["patterns"]:
                self.pattern_texts.append(preprocess(pattern))
                self.pattern_tags.append(tag)

        self.vectorizer = TfidfVectorizer()
        self.pattern_matrix = self.vectorizer.fit_transform(self.pattern_texts)

    @staticmethod
    def _load_intents(path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["intents"]

    def _match_intent(self, user_input: str):
        """Returns (response_or_None, tag_or_None, score)."""
        cleaned = preprocess(user_input)
        if not cleaned.strip():
            return None, None, 0.0

        user_vec = self.vectorizer.transform([cleaned])
        similarities = cosine_similarity(user_vec, self.pattern_matrix)[0]

        best_idx = similarities.argmax()
        best_score = float(similarities[best_idx])

        user_tokens = set(cleaned.split())
        pattern_tokens = set(self.pattern_texts[best_idx].split())
        overlap = user_tokens & pattern_tokens
        overlap_ratio = len(overlap) / max(len(user_tokens), 1)

        if best_score >= self.confidence_threshold and overlap_ratio >= 0.5:
            tag = self.pattern_tags[best_idx]
            response = random.choice(self.tag_to_responses[tag])
            return response, tag, best_score
        else:
            return None, None, best_score

    def get_response(self, user_input: str):
        """
        Try local NLP layers only (skills, then intents).
        Returns (response_or_None, source_tag_or_None, confidence_score).
        response is None if neither layer could answer confidently —
        callers should fall back to an external system (e.g. AI API) in that case.
        """
        skill_answer, skill_name = try_skills(user_input)
        if skill_answer:
            return skill_answer, skill_name, 1.0

        return self._match_intent(user_input)

    def backend_info(self) -> str:
        return "NLTK (full pipeline)" if using_nltk() else "fallback pure-Python tokenizer (NLTK unavailable)"
