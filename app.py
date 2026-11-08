
import os
import re
import requests

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()

MODEL = "@cf/meta/m2m100-1.2b"

API_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{ACCOUNT_ID}/ai/run/{MODEL}"
)

REQUEST_TIMEOUT = 30
MAX_TEXT_LENGTH = 1500
MAX_SENTENCES = 25


# =====================================================
# VERIFIED LANGUAGES (30)
# =====================================================
# Only languages that passed the round-trip test
# (English -> language -> English) in
# language_test_results.csv are listed here.
#
# Removed on purpose because the model produced wrong
# meaning, repeated words or random text for them:
# Catalan, Galician, Armenian, Thai, Burmese, Georgian,
# Lingala, Tswana, Yoruba, Fulah, Irish, Kazakh, Uzbek,
# Javanese, Sundanese, Zulu, Xhosa, Somali, Igbo, Hausa,
# Tamil, Malayalam, Kannada, Marathi, Sinhala, Nepali,
# Japanese (greeting came out as "good evening"), etc.

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ur": "Urdu",
    "hi": "Hindi",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "tr": "Turkish",
    "bn": "Bengali",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "el": "Greek",
    "he": "Hebrew",
    "hu": "Hungarian",
    "cs": "Czech",
    "ro": "Romanian",
    "id": "Indonesian",
    "ms": "Malay",
    "vi": "Vietnamese",
    "uk": "Ukrainian",
    "ko": "Korean",
    "hr": "Croatian"
}

# Languages written without spaces between sentences
NO_SPACE_LANGUAGES = {"zh"}

# Minimum chunk size (in characters) before a sentence is
# translated on its own. Chinese characters carry much more
# meaning each, so the limit is smaller.
MIN_CHUNK_LENGTH = 15
MIN_CHUNK_LENGTH_CJK = 5


# =====================================================
# TEXT PREPARATION
# =====================================================
# The model is much more accurate on one sentence at a
# time than on a long block, so long text is split into
# sentences, translated separately and joined again.

SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?\u061F\u06D4\u0964])\s+|(?<=[\u3002\uFF01\uFF1F])\s*"
)

def split_into_chunks(line, language="en"):

    joiner = "" if language in NO_SPACE_LANGUAGES else " "

    minimum = (
        MIN_CHUNK_LENGTH_CJK
        if language in NO_SPACE_LANGUAGES
        else MIN_CHUNK_LENGTH
    )

    parts = [
        part.strip()
        for part in SENTENCE_SPLIT_RE.split(line)
        if part and part.strip()
    ]

    # Very short pieces (like "Mr." or "Hi.") confuse the
    # model, so they are joined with the next sentence.

    chunks = []
    buffer = ""

    for part in parts:

        buffer = f"{buffer}{joiner}{part}" if buffer else part

        if len(buffer) >= minimum:
            chunks.append(buffer)
            buffer = ""

    if buffer:
        if chunks:
            chunks[-1] = f"{chunks[-1]}{joiner}{buffer}"
        else:
            chunks.append(buffer)

    return chunks


def looks_broken(output):

    # Detects the typical model failure where it repeats
    # one word again and again (for example "Hello Hello
    # Hello Hello").

    words = output.split()

    if len(words) < 5:
        return False

    longest_run = 1
    current_run = 1

    for previous, current in zip(words, words[1:]):

        if previous.lower() == current.lower():
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 1

    if longest_run >= 4:
        return True

    unique_ratio = len({w.lower() for w in words}) / len(words)

    return unique_ratio < 0.4


# =====================================================
# CLOUDFLARE TRANSLATION
# =====================================================

def call_cloudflare(text, source_language, target_language):

    payload = {
        "text": text,
        "source_lang": source_language,
        "target_lang": target_language
    }

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(
            "Translation service returned an invalid response."
        )

    if response.status_code == 401:
        raise RuntimeError(
            "Cloudflare authentication failed. "
            "Please check your API token."
        )

    if response.status_code == 403:
        raise RuntimeError(
            "Cloudflare denied access. "
            "Check your API token permissions."
        )

    if response.status_code == 429:
        raise RuntimeError(
            "Cloudflare rate limit reached. Please try again later."
        )

    if response.status_code != 200 or not result.get("success"):

        errors = result.get("errors", [])

        error_message = (
            errors[0].get("message")
            if errors and isinstance(errors, list)
            else "Translation service failed."
        )

        raise RuntimeError(error_message)

    data = result.get("result", {})

    translated_text = data.get("translated_text")

    if not isinstance(translated_text, str) or not translated_text.strip():
        raise RuntimeError(
            "Translation service returned empty text."
        )

    usage = data.get("usage", {})

    return translated_text.strip(), usage.get("neurons")


def translate_text(text, source_language, target_language):

    if not ACCOUNT_ID or not API_TOKEN:
        raise RuntimeError(
            "Cloudflare credentials are not configured."
        )

    lines = text.splitlines()

    jobs = []

    for line in lines:
        line = line.strip()
        jobs.append(
            split_into_chunks(line, source_language) if line else []
        )

    total_chunks = sum(len(chunks) for chunks in jobs)

    if total_chunks > MAX_SENTENCES:
        raise RuntimeError(
            f"Text is too long ({total_chunks} sentences). "
            f"Please translate at most {MAX_SENTENCES} sentences at a time."
        )

    separator = "" if target_language in NO_SPACE_LANGUAGES else " "

    translated_lines = []
    total_neurons = 0.0

    for chunks in jobs:

        translated_chunks = []

        for chunk in chunks:

            translated, neurons = call_cloudflare(
                chunk,
                source_language,
                target_language
            )

            if looks_broken(translated):
                raise RuntimeError(
                    "The translation looked unreliable for this text. "
                    "Please rewrite it as a complete, clear sentence "
                    "and try again."
                )

            translated_chunks.append(translated)

            if isinstance(neurons, (int, float)):
                total_neurons += neurons

        translated_lines.append(separator.join(translated_chunks))

    return {
        "translated_text": "\n".join(translated_lines).strip(),
        "neurons": round(total_neurons, 4)
    }


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    languages = [
        {"code": code, "name": name}
        for code, name in SUPPORTED_LANGUAGES.items()
    ]

    return render_template("index.html", languages=languages)


# =====================================================
# AVAILABLE LANGUAGES
# =====================================================

@app.route("/api/languages", methods=["GET"])
def get_languages():

    return jsonify({
        "status": "success",
        "languages": [
            {
                "code": code,
                "name": name
            }
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
    })


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "success",
        "service": "Lingua Studio",
        "translation_engine": MODEL,
        "languages": len(SUPPORTED_LANGUAGES),
        "credentials_configured": bool(
            ACCOUNT_ID and API_TOKEN
        ),
        "paid_fallback": False
    })


# =====================================================
# TRANSLATION API
# =====================================================

@app.route("/api/translate", methods=["POST"])
def translate():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "status": "error",
            "error": "Invalid request. JSON data is required."
        }), 400

    text = data.get("text")
    source_language = data.get("source_language")
    target_language = data.get("target_language")

    # Validate text

    if not isinstance(text, str) or not text.strip():

        return jsonify({
            "status": "error",
            "error": "Please enter text to translate."
        }), 400

    text = text.strip()

    if len(text) > MAX_TEXT_LENGTH:

        return jsonify({
            "status": "error",
            "error": (
                f"Text exceeds the maximum limit of "
                f"{MAX_TEXT_LENGTH} characters."
            )
        }), 400

    # Validate language codes

    if not isinstance(source_language, str):
        source_language = ""

    if not isinstance(target_language, str):
        target_language = ""

    source_language = source_language.strip().lower()
    target_language = target_language.strip().lower()

    # Compatibility with the old HTML dropdown

    if source_language == "zh-cn":
        source_language = "zh"

    if target_language == "zh-cn":
        target_language = "zh"

    if not source_language or not target_language:

        return jsonify({
            "status": "error",
            "error": "Please select both languages."
        }), 400

    if source_language not in SUPPORTED_LANGUAGES:

        return jsonify({
            "status": "error",
            "error": "Selected source language is not supported."
        }), 400

    if target_language not in SUPPORTED_LANGUAGES:

        return jsonify({
            "status": "error",
            "error": "Selected target language is not supported."
        }), 400

    if source_language == target_language:

        return jsonify({
            "status": "error",
            "error": "Source and target languages must be different."
        }), 400

    # Check API configuration

    if not ACCOUNT_ID or not API_TOKEN:

        return jsonify({
            "status": "error",
            "error": (
                "Translation service is not configured. "
                "Please check your .env file."
            )
        }), 503

    # Perform translation

    try:

        result = translate_text(
            text,
            source_language,
            target_language
        )

        return jsonify({
            "status": "success",
            "original_text": text,
            "translated_text": result["translated_text"],
            "source_language": source_language,
            "target_language": target_language,
            "usage": {
                "neurons": result["neurons"]
            }
        }), 200

    except requests.exceptions.Timeout:

        return jsonify({
            "status": "error",
            "error": (
                "Translation request timed out. "
                "Please try again."
            )
        }), 504

    except requests.exceptions.RequestException:

        app.logger.exception("Cloudflare connection error")

        return jsonify({
            "status": "error",
            "error": (
                "Could not connect to the translation service."
            )
        }), 502

    except RuntimeError as error:

        app.logger.warning("Translation error: %s", error)

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 502

    except Exception:

        app.logger.exception("Unexpected translation error")

        return jsonify({
            "status": "error",
            "error": "An unexpected server error occurred."
        }), 500


# =====================================================
# APPLICATION START
# =====================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )