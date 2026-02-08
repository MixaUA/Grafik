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
                
            text = text_area.get_text().lower()
            # Шукаємо повідомлення, де є згадка про графік
            if any(word in text for word in ["гпв", "графік", "черги"]):
                style = photo_wrap.get('style', '')
                match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if match:
                    img_url = match.group(1)
                    if img_url.startswith('//'): img_url = 'https:' + img_url
                    return {"url": img_url, "text": text}
        return None
    except Exception as e:
        print(f"❌ Помилка парсингу Telegram: {e}")
        return None

def main():
    msg_data = get_latest_msg_data()
    if not msg_data: return

    # Завантажуємо існуючу базу
    db_path = 'database_new.json'
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
            except:
                db = {}
    else:
        db = {}

    # Перевірка: чи ми вже обробляли цю картинку?
    if db.get("last_processed_url") == msg_data["url"]:
        print("⏭️ Цей графік вже є в базі. Пропускаємо сканування.")
        return

    img_data = requests.get(msg_data["url"]).content
    model_name = 'gemini-2.5-flash'
    
    # Промпт тепер просить ще й дату
    prompt = """
    Це таблиця графіку відключень світла ГПВ. 
    1. Знайди дату, на яку цей графік (наприклад, 09.02.2026).
    2. Для кожної підчерги (1.1-6.2) випиши ВСІ часові інтервали.
    Поверни ТІЛЬКИ JSON:
    {
      "date": "ДД.ММ.РРРР",
      "queues": {
        "1.1": ["час-час", "час-час"],
        ...
      }
    }
    """
    
    print(f"🤖 Новий графік знайдено! AI розшифровує через {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': img_data}])
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            new_data = json.loads(json_match.group())
            date_key = new_data.get("date", datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m.%Y"))
            
            # Оновлюємо базу: додаємо новий день, зберігаючи старі
            if "days" not in db: db["days"] = {}
            db["days"][date_key] = {
                "queues": new_data["queues"],
                "updated_at": datetime.now(ZoneInfo("Europe/Kiev")).strftime("%H:%M")
            }
            
            # Запам'ятовуємо URL, щоб не сканувати знову
            db["last_processed_url"] = msg_data["url"]
            
            # Видаляємо старі дати (наприклад, залишаємо лише останні 3 дні), щоб файл не ріс вічно
            keys = sorted(db["days"].keys(), reverse=True)
            db["days"] = {k: db["days"][k] for k in keys[:3]}

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            print(f"🎉 Графік на {date_key} додано до бази!")
        else:
            print("❌ AI не повернув JSON.")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
