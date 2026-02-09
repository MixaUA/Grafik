import os
import json
import requests
import re
from google import genai
from google.genai import types  # Додано для правильної типізації даних
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Ініціалізація клієнта
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def get_ua_date(date_str):
    months = {
        "01": "січня", "02": "лютого", "03": "березня", "04": "квітня",
        "05": "травня", "06": "червня", "07": "липня", "08": "серпня",
        "09": "вересня", "10": "жовтня", "11": "листопада", "12": "грудня"
    }
    try:
        day, month, _ = date_str.split('.')
        return f"{int(day)} {months.get(month, month)}"
    except:
        return date_str

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
    if not msg_data: return

    db_path = 'database.json'
    db = {}
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    if db.get("last_processed_url") == msg_data["url"]:
        print(f"☕ Змін немає.")
        return

    print(f"🤖 Новий графік знайдено! AI розшифровує через виправлений SDK...")

    img_data = requests.get(msg_data["url"]).content
    
    prompt = """
    Це таблиця ГПВ. Визнач дату (DD.MM.YYYY) та день тижня.
    Витягни інтервали для ВСІХ підчерг 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 6.1, 6.2.
    Поверни ТІЛЬКИ JSON об'єкт з полями date, day_of_week та queues.
    """
    
    try:
        # ВИПРАВЛЕНО: Використовуємо types.Part для передачі медіа-даних
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(data=img_data, mime_type='image/jpeg')
            ]
        )
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            res = json.loads(json_match.group())
            ua_days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            kyiv_now = datetime.now(ZoneInfo("Europe/Kiev"))
            all_q_names = [f"{i}.{j}" for i in range(1, 7) for j in range(1, 3)]
            
            if "queues" not in db:
                db["queues"] = {q: {d: [] for d in ua_days} for q in all_q_names}

            today_name = ua_days[kyiv_now.weekday()]
            tomorrow_name = ua_days[(kyiv_now.weekday() + 1) % 7]
            for q in db["queues"]:
                for d in ua_days:
                    if d != today_name and d != tomorrow_name:
                        db["queues"][q][d] = []

            target_day = res.get('day_of_week', today_name).lower()
            queues_source = res.get('queues', res)
            for q_name in all_q_names:
                if q_name in queues_source:
                    data = queues_source[q_name]
                    db["queues"][q_name][target_day] = data if isinstance(data, list) else []

            display_date = get_ua_date(res.get('date', kyiv_now.strftime("%d.%m.%Y")))
            
            output = {
                "update_time": f"{display_date} {kyiv_now.strftime('%H:%M')}",
                "queues": db["queues"],
                "last_processed_url": msg_data["url"],
                "last_processed_text": msg_data["text"]
            }

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"🎉 Дані на {display_date} оновлено!")
        else:
            print("❌ AI не повернув JSON.")
    except Exception as e:
        print(f"❌ Помилка роботи з Gemini: {e}")

if __name__ == "__main__":
    main()
