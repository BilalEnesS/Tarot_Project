from flask import Flask, render_template, request
import random
import json
import os
from openai import OpenAI
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

app = Flask(__name__)

# Flask-Limiter başlat
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute"]  # Tüm uygulama için genel limit
)

# OpenAI API anahtarını ortamdan al
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY ortam değişkeni tanımlı değil!")
client = OpenAI(api_key=OPENAI_API_KEY)

# Kart verilerini yükle
with open("tarot-images.json", "r", encoding="utf-8") as f:
    cards_data = json.load(f)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/draw", methods=["POST"])
def draw():
    selected_cards = random.sample(cards_data["cards"], 6)
    descriptions = []
    for card in selected_cards:
        desc = f"Kart: {card['name']}\nAnlam (aydınlık): {card['meanings']['light']}\nAnlam (gölge): {card['meanings']['shadow']}\nAnahtar Kelimeler: {', '.join(card['keywords'])}\n"
        descriptions.append(desc)
    prompt = "Sen bir tarot uzmanısın. Kullanıcı aşağıdaki 6 kartı çekti:\n\n"
    prompt += "\n".join(descriptions)
    prompt += "\n\nBu 6 kartı birlikte yorumla ve mistik ama pozitif bir dille genel bir tarot açılımı yap. Cevabını Türkçe yaz."
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Sen yardımsever ve spiritüel bir tarot yorumcususun. Cevaplarını Türkçe ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        gpt_response = response.choices[0].message.content
    except Exception as e:
        gpt_response = f"Bir hata oluştu: {e}"
    # Kartların sadece gerekli alanlarını gönder
    cards = [{"name": c["name"], "img": c["img"]} for c in selected_cards]
    return {"cards": cards, "gpt_text": gpt_response}

@app.route("/draw-cards", methods=["POST"])
def draw_cards():
    selected_cards = random.sample(cards_data["cards"], 6)
    cards = [{"name": c["name"], "img": c["img"], "meanings": c["meanings"], "keywords": c["keywords"]} for c in selected_cards]
    return {"cards": cards}

@app.route("/draw-comment", methods=["POST"])
@limiter.limit("3 per minute")  # Her IP için dakikada 3 istek
def draw_comment():
    data = request.get_json()
    cards = data.get("cards", [])
    descriptions = []
    for card in cards:
        desc = f"Kart: {card['name']}\nAnlam (aydınlık): {card['meanings']['light']}\nAnlam (gölge): {card['meanings']['shadow']}\nAnahtar Kelimeler: {', '.join(card['keywords'])}\n"
        descriptions.append(desc)
    prompt = "Sen bir tarot uzmanısın. Kullanıcı aşağıdaki 6 kartı çekti:\n\n"
    prompt += "\n".join(descriptions)
    prompt += "\n\nBu 6 kartı birlikte yorumla ve mistik ama pozitif bir dille genel bir tarot açılımı yap. Cevabını Türkçe yaz."
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Sen yardımsever ve spiritüel bir tarot yorumcususun. Cevaplarını Türkçe ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        gpt_response = response.choices[0].message.content
    except Exception as e:
        gpt_response = f"Bir hata oluştu: {e}"
    return {"gpt_text": gpt_response}

@app.errorhandler(429)
def ratelimit_handler(e):
    return {"error": "Çok fazla istek gönderdiniz. Lütfen biraz bekleyin."}, 429

if __name__ == "__main__":
    app.run(debug=True)
