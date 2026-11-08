
import os
import csv
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/meta/m2m100-1.2b"

API_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{ACCOUNT_ID}/ai/run/{MODEL}"
)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Cloudflare Free daily allocation: 10,000 neurons.
# Stop at 8,000 to maintain a safety margin.
MAX_NEURONS = 8000

# English reference sentence
ENGLISH_TEXT = "Good morning. How are you today?"

# --------------------------------------------------
# M2M100 LANGUAGE INVENTORY
# --------------------------------------------------

LANGUAGES = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "ast": "Asturian",
    "az": "Azerbaijani",
    "ba": "Bashkir",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "br": "Breton",
    "bs": "Bosnian",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "ff": "Fulah",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Western Frisian",
    "ga": "Irish",
    "gd": "Scottish Gaelic",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "ht": "Haitian Creole",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "ig": "Igbo",
    "ilo": "Iloko",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Central Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "lb": "Luxembourgish",
    "lg": "Ganda",
    "ln": "Lingala",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "my": "Burmese",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "ns": "Northern Sotho",
    "oc": "Occitan",
    "or": "Oriya",
    "pa": "Panjabi",
    "pl": "Polish",
    "ps": "Pashto",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "ss": "Swati",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "th": "Thai",
    "tl": "Tagalog",
    "tn": "Tswana",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "wo": "Wolof",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zh": "Chinese",
    "zu": "Zulu"
}

# --------------------------------------------------
# TEST STATE
# --------------------------------------------------

total_neurons = 0
successful = 0
failed = 0
stopped = False

CSV_FILE = BASE_DIR / "language_test_results.csv"

# --------------------------------------------------
# TRANSLATION FUNCTION
# --------------------------------------------------

def translate(text, source, target):

    payload = {
        "text": text,
        "source_lang": source,
        "target_lang": target
    }

    response = requests.post(
        API_URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    try:
        data = response.json()
    except ValueError:
        return {
            "success": False,
            "error": "Invalid JSON response",
            "neurons": None,
            "translation": ""
        }

    if response.status_code == 200 and data.get("success"):

        result = data.get("result", {})
        usage = result.get("usage", {})

        return {
            "success": True,
            "translation": result.get("translated_text", ""),
            "neurons": usage.get("neurons"),
            "error": ""
        }

    return {
        "success": False,
        "translation": "",
        "neurons": None,
        "error": str(data.get("errors", data))
    }


# --------------------------------------------------
# SAVE RESULT
# --------------------------------------------------

def save_result(writer, language, code, direction,
                original, translated, status, neurons, error):

    writer.writerow([
        language,
        code,
        direction,
        original,
        translated,
        status,
        neurons,
        error
    ])


# --------------------------------------------------
# MAIN TESTING
# --------------------------------------------------

def main():

    global total_neurons, successful, failed, stopped

    if not ACCOUNT_ID or not API_TOKEN:
        print("ERROR: Cloudflare credentials missing.")
        return

    if len(LANGUAGES) != 100:
        print("ERROR: Language inventory is not 100.")
        return

    print("\nLINGUA STUDIO")
    print("M2M100 COMPLETE LANGUAGE SCREENING")
    print("Model:", MODEL)
    print("Languages:", len(LANGUAGES))
    print("Reference:", "English")
    print("Maximum neuron budget:", MAX_NEURONS)

    print("\nExpected API requests: 198")
    print("Results file:", CSV_FILE.name)

    print("\nStarting tests...\n")

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Language",
            "Language Code",
            "Direction",
            "Original Text",
            "Translation",
            "Status",
            "Neurons",
            "Error"
        ])

        for code, language in LANGUAGES.items():

            if code == "en":
                continue

            if stopped:
                break

            print("\n" + "=" * 55)
            print("LANGUAGE:", language, f"({code})")

            # -----------------------------
            # TEST 1: English -> Target
            # -----------------------------

            print("\nEnglish ->", language)

            try:
                first = translate(
                    ENGLISH_TEXT,
                    "en",
                    code
                )

            except requests.exceptions.RequestException as error:
                first = {
                    "success": False,
                    "translation": "",
                    "neurons": None,
                    "error": str(error)
                }

            if first["neurons"] is None:
                failed += 1
                print("FAILED:", first["error"])

                save_result(
                    writer, language, code,
                    "en->" + code, ENGLISH_TEXT,
                    "", "FAILED", "", first["error"]
                )

                file.flush()
                continue

            total_neurons += float(first["neurons"])

            if total_neurons >= MAX_NEURONS:
                stopped = True
                print("Neuron safety limit reached.")
                break

            if first["success"] and first["translation"]:

                successful += 1
                translated_text = first["translation"]

                print("Translation:", translated_text)
                print("Neurons:", first["neurons"])

                save_result(
                    writer, language, code,
                    "en->" + code, ENGLISH_TEXT,
                    translated_text, "SUCCESS",
                    first["neurons"], ""
                )

                file.flush()

                # -----------------------------
                # TEST 2: Target -> English
                # -----------------------------

                print("\n", language, "-> English")

                try:
                    second = translate(
                        translated_text,
                        code,
                        "en"
                    )

                except requests.exceptions.RequestException as error:
                    second = {
                        "success": False,
                        "translation": "",
                        "neurons": None,
                        "error": str(error)
                    }

                if second["neurons"] is None:
                    failed += 1
                    print("FAILED:", second["error"])

                    save_result(
                        writer, language, code,
                        code + "->en", translated_text,
                        "", "FAILED", "", second["error"]
                    )

                    file.flush()
                    continue

                total_neurons += float(second["neurons"])

                if total_neurons >= MAX_NEURONS:
                    stopped = True
                    print("Neuron safety limit reached.")
                    break

                if second["success"]:
                    successful += 1
                    print("Back translation:", second["translation"])

                    save_result(
                        writer, language, code,
                        code + "->en", translated_text,
                        second["translation"], "SUCCESS",
                        second["neurons"], ""
                    )

                else:
                    failed += 1
                    print("FAILED:", second["error"])

                    save_result(
                        writer, language, code,
                        code + "->en", translated_text,
                        "", "FAILED", second["neurons"],
                        second["error"]
                    )

            else:
                failed += 1

                save_result(
                    writer, language, code,
                    "en->" + code, ENGLISH_TEXT,
                    "", "FAILED", first["neurons"],
                    first["error"]
                )

            file.flush()

            # Small pause between language pairs
            time.sleep(0.5)

    # --------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------

    print("\n" + "=" * 55)
    print("FINAL TEST REPORT")
    print("=" * 55)

    print("Languages in inventory:", len(LANGUAGES))
    print("Languages tested:", successful // 2)
    print("Successful requests:", successful)
    print("Failed requests:", failed)
    print("Total neurons:", round(total_neurons, 3))
    print("CSV saved:", CSV_FILE.name)

    if stopped:
        print("STATUS: STOPPED AT SAFETY LIMIT")
    else:
        print("STATUS: TESTING COMPLETED")

    print("\nTechnical screening only.")
    print("Human quality review is still required.")


if __name__ == "__main__":
    main()
