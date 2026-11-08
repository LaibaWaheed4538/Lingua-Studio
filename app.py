from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# MyMemory Translation API
TRANSLATION_API_URL = "https://api.mymemory.translated.net/get"


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/translate", methods=["POST"])
def translate():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid request. JSON data is required."
        }), 400

    text = data.get("text", "").strip()
    source_language = data.get("source_language", "").strip()
    target_language = data.get("target_language", "").strip()

    if not text:
        return jsonify({
            "error": "Please enter text to translate."
        }), 400

    if not source_language or not target_language:
        return jsonify({
            "error": "Please select both source and target languages."
        }), 400

    if source_language == target_language:
        return jsonify({
            "error": "Source and target languages must be different."
        }), 400

    # MyMemory allows a maximum of 500 bytes per request.
    if len(text.encode("utf-8")) > 500:
        return jsonify({
            "error": "Text is too long. Maximum allowed size is 500 bytes per request."
        }), 400

    parameters = {
        "q": text,
        "langpair": f"{source_language}|{target_language}"
    }

    try:
        response = requests.get(
            TRANSLATION_API_URL,
            params=parameters,
            timeout=20
        )

        response.raise_for_status()

        result = response.json()

        if result.get("quotaFinished"):
            return jsonify({
                "error": "Daily free translation limit has been reached."
            }), 429

        if result.get("responseStatus") != 200:
            return jsonify({
                "error": result.get(
                    "responseDetails",
                    "Translation service returned an error."
                )
            }), 502

        translated_text = result.get(
            "responseData", {}
        ).get("translatedText")

        if not translated_text:
            return jsonify({
                "error": "No translated text was received."
            }), 502

        return jsonify({
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language,
            "status": "success"
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Translation service took too long to respond."
        }), 504

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Could not connect to the translation service."
        }), 502

    except ValueError:
        return jsonify({
            "error": "Invalid response received from translation service."
        }), 502


if __name__ == "__main__":
    app.run(debug=True)