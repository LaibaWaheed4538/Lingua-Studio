
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/meta/m2m100-1.2b"

URL = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{ACCOUNT_ID}/ai/run/{MODEL}"
)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Multiple language and sentence quality tests
LANGUAGE_TESTS = [
    {
        "language": "Urdu",
        "code": "ur",
        "word": "Beautiful",
        "short": "How are you today?",
        "long": "Although it was raining heavily, we decided to visit the university because our final examination was scheduled for the following morning.",
        "reverse": "مجھے نئی زبانیں سیکھنا اور مختلف ثقافتوں کے بارے میں جاننا پسند ہے۔"
    },
    {
        "language": "Chinese",
        "code": "zh",
        "word": "Beautiful",
        "short": "Where are you going?",
        "long": "Although the weather was cold, the students continued studying together because they wanted to prepare well for their examinations.",
        "reverse": "今天天气很好，我想和朋友一起去公园散步。"
    },
    {
        "language": "French",
        "code": "fr",
        "word": "Beautiful",
        "short": "I will see you tomorrow.",
        "long": "Although I was very tired after work, I decided to finish my assignment before going to sleep.",
        "reverse": "Bonjour, comment allez-vous aujourd'hui ?"
    },
    {
        "language": "German",
        "code": "de",
        "word": "Beautiful",
        "short": "Where is the nearest hospital?",
        "long": "If we manage our time properly and work together, we can complete this project before the deadline.",
        "reverse": "Guten Morgen, ich hoffe, dass Sie einen schönen Tag haben."
    },
    {
        "language": "Spanish",
        "code": "es",
        "word": "Beautiful",
        "short": "Thank you for your support.",
        "long": "The university organized an international conference where students and researchers discussed new scientific discoveries.",
        "reverse": "Me gusta aprender idiomas y conocer diferentes culturas."
    },
    {
        "language": "Italian",
        "code": "it",
        "word": "Beautiful",
        "short": "How much does this cost?",
        "long": "Even though the train was delayed, we arrived at the airport early enough to catch our flight.",
        "reverse": "Buongiorno, vorrei imparare una nuova lingua."
    },
    {
        "language": "Russian",
        "code": "ru",
        "word": "Beautiful",
        "short": "Can you help me?",
        "long": "Technology has changed the way people communicate, work, study and share information around the world.",
        "reverse": "Спасибо за вашу помощь, я очень это ценю."
    },
    {
        "language": "Arabic",
        "code": "ar",
        "word": "Beautiful",
        "short": "Where are you from?",
        "long": "Education is essential for building a better future because it gives people knowledge, confidence and opportunities.",
        "reverse": "أحب تعلم اللغات والتعرف على ثقافات مختلفة."
    },
    {
        "language": "Hindi",
        "code": "hi",
        "word": "Beautiful",
        "short": "What are you doing?",
        "long": "Students should develop good study habits and practice regularly if they want to achieve their academic goals.",
        "reverse": "मुझे नई भाषाएँ सीखना और किताबें पढ़ना पसंद है।"
    },
    {
        "language": "Bengali",
        "code": "bn",
        "word": "Beautiful",
        "short": "I need your help.",
        "long": "Reading books regularly improves our knowledge, develops our thinking skills and helps us understand the world.",
        "reverse": "আমি নতুন ভাষা শিখতে এবং বই পড়তে ভালোবাসি।"
    },
    {
        "language": "Japanese",
        "code": "ja",
        "word": "Beautiful",
        "short": "Thank you very much.",
        "long": "Learning a new language requires patience, regular practice and an understanding of different cultures.",
        "reverse": "今日は天気がいいので、友達と公園に行きたいです。"
    },
    {
        "language": "Korean",
        "code": "ko",
        "word": "Beautiful",
        "short": "Where is the railway station?",
        "long": "Students who practice consistently and ask questions when they do not understand something usually improve their skills.",
        "reverse": "저는 새로운 언어를 배우고 다양한 문화를 이해하는 것을 좋아합니다."
    },
    {
        "language": "Turkish",
        "code": "tr",
        "word": "Beautiful",
        "short": "I am learning a new language.",
        "long": "Although the journey was long, we enjoyed every moment because we discovered many interesting places.",
        "reverse": "Bugün hava çok güzel ve arkadaşlarımla yürüyüş yapmak istiyorum."
    },
    {
        "language": "Portuguese",
        "code": "pt",
        "word": "Beautiful",
        "short": "I will call you later.",
        "long": "The development of modern technology has created new opportunities for education, communication and international business.",
        "reverse": "Gosto de aprender novos idiomas e conhecer outras culturas."
    },
    {
        "language": "Indonesian",
        "code": "id",
        "word": "Beautiful",
        "short": "What time is it?",
        "long": "Good communication and teamwork are important because they help people solve problems and achieve common goals.",
        "reverse": "Saya suka belajar bahasa baru dan membaca buku setiap hari."
    }
]


def translate(text, source, target):

    payload = {
        "text": text,
        "source_lang": source,
        "target_lang": target
    }

    try:
        response = requests.post(
            URL,
            headers=HEADERS,
            json=payload,
            timeout=60
        )

        try:
            result = response.json()
        except ValueError:
            return {
                "success": False,
                "error": "Invalid JSON response"
            }

        if response.ok and result.get("success"):

            data = result.get("result", {})

            return {
                "success": True,
                "translation": data.get("translated_text"),
                "neurons": data.get("usage", {}).get("neurons")
            }

        return {
            "success": False,
            "error": result.get("errors", result)
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "error": str(error)
        }


def run_test(name, text, source, target):

    print("\n" + "=" * 65)
    print("TEST:", name)
    print(f"LANGUAGE: {source} -> {target}")
    print("ORIGINAL:", text)

    result = translate(text, source, target)

    if result["success"]:
        print("TRANSLATION:", result["translation"])
        print("NEURONS:", result["neurons"])
        print("STATUS: SUCCESS")
    else:
        print("STATUS: FAILED")
        print("ERROR:", result["error"])

    return result["success"]


def main():

    if not ACCOUNT_ID or not API_TOKEN:
        print("ERROR: Cloudflare credentials missing.")
        return

    print("\nLINGUA STUDIO - MULTILINGUAL QUALITY TEST")
    print("MODEL:", MODEL)
    print("LANGUAGES:", len(LANGUAGE_TESTS))

    total = 0
    successful = 0

    for item in LANGUAGE_TESTS:

        language = item["language"]
        code = item["code"]

        # English to target language:
        tests = [
            ("Single Word", item["word"]),
            ("Short Sentence", item["short"]),
            ("Long Sentence", item["long"])
        ]

        for test_name, sentence in tests:

            total += 1

            if run_test(
                f"{language} - {test_name}",
                sentence,
                "en",
                code
            ):
                successful += 1

        # Target language to English:
        total += 1

        if run_test(
            f"{language} - Reverse Translation",
            item["reverse"],
            code,
            "en"
        ):
            successful += 1

    print("\n" + "=" * 65)
    print("FINAL TEST REPORT")
    print("=" * 65)
    print("Total Requests:", total)
    print("Successful Requests:", successful)
    print("Failed Requests:", total - successful)
    print("Technical Success Rate:", f"{successful / total * 100:.1f}%")
    print("\nALL TESTS COMPLETED")


if __name__ == "__main__":
    main()
