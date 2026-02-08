import os
import json
import requests
import re
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Налаштування Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def get_latest_msg_data():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
            if not photo_wrap or not text_area: continue
                
            text = text_area.get_text().strip()
            if any(word in text.lower() for word in ["гпв", "графік", "черги"]):
                style = photo_wrap.get('style', '')
                match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if match:
                    img_url = match.group(1)
                    if img_url.startswith('//'): img_url = 'https:' + img_url
                    return {"url": img_url, "text": text}
        return None
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
        return None

def main():
    msg_data = get_latest_msg_data()
    if not msg_data:
        print("🔍 Повідомлень з графіком не знайдено.")
        return

    db_path = 'database_new.json'
    db = {}
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    # Дебаг логіки змін
    is_same_url = db.get("last_processed_url") == msg_data["url"]
    is_same_text = db.get("last_processed_text") == msg_data["text"]

    if is_same_url and is_same_text:
        print(f"☕ Gemini НЕ запускається: цей графік ({msg_data['url']}) вже оброблено.")
        return

    print(f"🤖 Gemini ЗАПУСКАЄТЬСЯ: знайдено новий або змінений графік.")

    img_data = requests.get(msg_data["url"]).content
    model_name = 'gemini-2.5-flash'
    
    # Промпт адаптований під твій формат JSON (з днями тижня)
    prompt = """
    Це таблиця ГПВ. Визнач дату (напр. 09.02.2026) та день тижня для цієї дати (напр. понеділок).
    Витягни інтервали відключень для підчерг 1.1-6.2.
    Поверни ТІЛЬКИ JSON у такому форматі:
    {
      "date": "09.02.2026",
      "day_of_week": "понеділок",
      "queues": {
        "1.1": {
          "понеділок": ["00:00-02:00", "04:00-08:00"],
          "вівторок": [], "середа": [], "четвер": [], "п'ятниця": [], "субота": [], "неділя": []
        }
      }
    }
    Важливо: Заповни інтервали ТІЛЬКИ для того дня тижня, якому відповідає дата графіка. Всі інші дні мають бути порожніми списками [].
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': img_data}])
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            res = json.loads(json_match.group())
            
            # Формуємо структуру як на сайті
            update_time = f"{res['date'][:5]} {datetime.now(ZoneInfo('Europe/Kiev')).strftime('%H:%M')}"
            
            output = {
                "update_time": update_time,
                "queues": res["queues"],
                "last_processed_url": msg_data["url"],
                "last_processed_text": msg_data["text"]
            }

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"🎉 Дані на {res['date']} ({res['day_of_week']}) успішно збережені у форматі сайту.")
        else:
            print("❌ AI повернув некоректні дані.")
    except Exception as e:
        print(f"❌ Помилка AI: {e}")

if __name__ == "__main__":
    main()
