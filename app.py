
import os
import requests

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024

ENGINE = "DeepL API (Free)"

MAX_TEXT_LENGTH = 1500

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "").strip()

DEEPL_BASE_URL = "https://api-free.deepl.com"

REQUEST_TIMEOUT = 30


# =====================================================
# LANGUAGE CACHE
# =====================================================

SOURCE_LANGUAGES = []
TARGET_LANGUAGES = []


def fetch_languages():

    global SOURCE_LANGUAGES, TARGET_LANGUAGES

    if not DEEPL_API_KEY:
        raise RuntimeError("DeepL API key is missing from .env file.")

    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
    }

    try:

        # Fetch source languages

        source_response = requests.get(
            f"{DEEPL_BASE_URL}/v2/languages",
            params={"type": "source"},
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        source_response.raise_for_status()

        # Fetch target languages

        target_response = requests.get(
            f"{DEEPL_BASE_URL}/v2/languages",
            params={"type": "target"},
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        target_response.raise_for_status()

        SOURCE_LANGUAGES = [
            {
                "code": item["language"],
                "name": item["name"]
            }
            for item in source_response.json()
        ]

        TARGET_LANGUAGES = [
            {
                "code": item["language"],
                "name": item["name"]
            }
            for item in target_response.json()
        ]

        app.logger.info(
            "Loaded %s source and %s target languages.",
            len(SOURCE_LANGUAGES),
            len(TARGET_LANGUAGES)
        )

    except requests.RequestException as error:

        app.logger.exception("Could not load DeepL languages.")

        raise RuntimeError(
            "Unable to retrieve supported languages from DeepL."
        ) from error


# =====================================================
# LANGUAGE CODE NORMALIZATION
# =====================================================

LANGUAGE_CODE_MAP = {
    "zh-cn": "ZH-HANS",
    "zh": "ZH",
    "zh-tw": "ZH-HANT",
    "en": "EN",
    "pt": "PT-BR"
}


def normalize_language(code):
    return code.strip().upper()

# =====================================================
# DEEPL TRANSLATION
# =====================================================

def translate_text(text, source_language, target_language):

    if not DEEPL_API_KEY:
        raise RuntimeError(
            "DeepL API key is missing. Check your .env file."
        )

    source = normalize_language(source_language)
    target = normalize_language(target_language)

    available_sources = {
        item["code"] for item in SOURCE_LANGUAGES
    }

    available_targets = {
        item["code"] for item in TARGET_LANGUAGES
    }

    if source not in available_sources:

        raise RuntimeError(
            "Selected source language is not supported by DeepL."
        )

    if target not in available_targets:

        raise RuntimeError(
            "Selected target language is not supported by DeepL."
        )

    if source == target:

        raise RuntimeError(
            "Source and target languages must be different."
        )

    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": [text],
        "source_lang": source,
        "target_lang": target
    }

    try:

        response = requests.post(
            f"{DEEPL_BASE_URL}/v2/translate",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 429:
            raise RuntimeError(
                "DeepL request limit reached. Please try again later."
            )

        if response.status_code == 456:
            raise RuntimeError(
                "DeepL free usage limit has been reached."
            )

        if response.status_code == 403:
            raise RuntimeError(
                "DeepL API authentication failed. Check your API key."
            )

        if response.status_code == 400:
            raise RuntimeError(
                "Invalid translation request or unsupported language pair."
            )

        if response.status_code >= 500:
            raise RuntimeError(
                "DeepL service is temporarily unavailable."
            )

        response.raise_for_status()

        result = response.json()

        translations = result.get("translations", [])

        if not translations:

            raise RuntimeError(
                "DeepL returned an empty translation."
            )

        translated_text = translations[0].get("text", "")

        if not translated_text.strip():

            raise RuntimeError(
                "DeepL returned empty text."
            )

        return translated_text.strip()

    except requests.Timeout:

        raise RuntimeError(
            "DeepL request timed out. Please try again."
        )

    except requests.ConnectionError:

        raise RuntimeError(
            "Could not connect to DeepL. Check your internet connection."
        )

    except requests.RequestException as error:

        app.logger.exception("DeepL API request failed.")

        raise RuntimeError(
            "Translation service request failed."
        ) from error


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    try:
        if not SOURCE_LANGUAGES or not TARGET_LANGUAGES:
            fetch_languages()

        return render_template(
            "index.html",
            source_languages=SOURCE_LANGUAGES,
            target_languages=TARGET_LANGUAGES
        )

    except RuntimeError as error:
        app.logger.error("Language loading failed: %s", error)

        return render_template(
            "index.html",
            source_languages=[],
            target_languages=[]
        )

# =====================================================
# AVAILABLE LANGUAGES
# =====================================================

@app.route("/api/languages", methods=["GET"])
def get_languages():

    try:

        if not SOURCE_LANGUAGES or not TARGET_LANGUAGES:
            fetch_languages()

        return jsonify({

            "status": "success",

            "source_languages": SOURCE_LANGUAGES,

            "target_languages": TARGET_LANGUAGES,

            # Compatibility with existing language lists
            "languages": TARGET_LANGUAGES

        }), 200

    except RuntimeError as error:

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 502


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({

        "status": "success",

        "service": "Lingua Studio",

        "translation_engine": ENGINE,

        "api_key_configured": bool(DEEPL_API_KEY)

    }), 200


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

    source_language = source_language.strip()
    target_language = target_language.strip()

    if not source_language or not target_language:

        return jsonify({
            "status": "error",
            "error": "Please select both languages."
        }), 400

    # Normalize codes

    source_language = normalize_language(source_language)

    target_language = normalize_language(target_language)

    # Load language lists if necessary

    try:

        if not SOURCE_LANGUAGES or not TARGET_LANGUAGES:
            fetch_languages()

        # Perform translation

        translated_text = translate_text(
            text,
            source_language,
            target_language
        )

        return jsonify({

            "status": "success",

            "original_text": text,

            "translated_text": translated_text,

            "source_language": source_language,

            "target_language": target_language

        }), 200

    except RuntimeError as error:

        app.logger.warning(
            "Translation error: %s", error
        )

        return jsonify({

            "status": "error",

            "error": str(error)

        }), 502

    except Exception:

        app.logger.exception(
            "Unexpected translation error."
        )

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
