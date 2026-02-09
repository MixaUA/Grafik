import os
import json
import requests
import re
import time
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Конфігурація моделі та часового поясу
MODEL_NAME = 'gemini-2.5-flash' 
kyiv_tz = ZoneInfo("Europe/Kiev")
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def get_ua_date(date_str):
    """Перетворює дату DD.MM.YYYY у формат '9 лютого'"""
    months = {"01":"січня","02":"лютого","03":"березня","04":"квітня","05":"травня","06":"червня","07":"липня","08":"серпня","09":"вересня","10":"жовтня","11":"листопада","12":"грудня"}
    try:
        day, month, _ = date_str.split('.')
        return f"{int(day)} {months.get(month, month)}"
    except: return date_str

def extract_data_from_msg(msg):
    """Витягує текст та URL фото з повідомлення Telegram"""
    text_area = msg.find('div', class_='tgme_widget_message_text')
    photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
    if photo_wrap and text_area:
        text = text_area.get_text().strip()
        if any(word in text.lower() for word in ["гпв", "графік", "черги"]):
            style = photo_wrap.get('style', '')
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if match:
                img_url = match.group(1)
                if img_url.startswith('//'): img_url = 'https:' + img_url
                return {"url": img_url, "text": text}
    return None

def get_latest_msg_data():
    """Шукає актуальний графік у закріпах або стрічці"""
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Пріоритет закріпленим повідомленням
        pinned_msg = soup.find('div', class_='tgme_widget_message_pinned')
        if pinned_msg:
            data = extract_data_from_msg(pinned_msg)
            if data: return data

        # 2. Якщо в закріпах немає - стрічка
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        for msg in reversed(messages):
            data = extract_data_from_msg(msg)
            if data: return data
        return None
    except Exception: return None

def main():
    db_path = 'database.json'
    kyiv_now = datetime.now(kyiv_tz)
    ua_days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
    
    today_name = ua_days[kyiv_now.weekday()]
    tomorrow_name = ua_days[(kyiv_now + timedelta(days=1)).weekday()]

    db = {}
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    # Захист від лімітів 429
    retry_after = db.get("retry_after")
    if retry_after and time.time() < retry_after:
        return

    msg_data = get_latest_msg_data()
    if not msg_data or db.get("last_processed_url") == msg_data["url"]:
        print("☕ Змін немає, графік той самий.")
        return

    try:
        img_data = requests.get(msg_data["url"]).content
        # Промпт фокусується лише на цифрах та даті
        prompt = (
            "Це таблиця ГПВ. Твоє завдання:\n"
            "1. Визнач дату (DD.MM.YYYY).\n"
            "2. Витягни часові інтервали відключень для кожної підчерги 1.1-6.2.\n"
            "Поверни JSON: {'date': 'DD.MM.YYYY', 'queues': {'1.1': ['00:00-02:00'], ...}}"
        )
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[types.Part.from_text(text=prompt), types.Part.from_bytes(data=img_data, mime_type='image/jpeg')]
        )
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            res = json.loads(json_match.group())
            source = res.get('queues', res)
            
            # --- РОЗУМНЕ ВИЗНАЧЕННЯ ДНЯ ТИЖНЯ ---
            raw_date = res.get('date', kyiv_now.strftime("%d.%m.%Y"))
            try:
                # Python обчислює день тижня на основі знайденої дати
                date_obj = datetime.strptime(raw_date, "%d.%m.%Y").replace(tzinfo=kyiv_tz)
                target_day = ua_days[date_obj.weekday()]
            except:
                target_day = today_name
            
            # --- ПЕРЕЗБІРКА БАЗИ (Сьогодні + Завтра) ---
            all_q_names = [f"{i}.{j}" for i in range(1, 7) for j in range(1, 3)]
            new_queues = {q: {d: [] for d in ua_days} for q in all_q_names}
            
            # Копіюємо старі дані, якщо вони ще актуальні
            if "queues" in db:
                for q in all_q_names:
                    for d in [today_name, tomorrow_name]:
                        if d in db["queues"][q]:
                            new_queues[q][d] = db["queues"][q][d]

            # Записуємо нові дані від ШІ у правильну «комірку»
            for q in all_q_names:
                if q in source and source[q]:
                    new_queues[q][target_day] = source[q]

            display_date = get_ua_date(raw_date)
            
            output = {
                "update_time": f"{display_date} {kyiv_now.strftime('%H:%M')}",
                "queues": new_queues,
                "last_processed_url": msg_data["url"],
                "last_processed_text": msg_data["text"]
            }

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"🎉 Графік на {raw_date} ({target_day}) оновлено!")

    except Exception as e:
        if "429" in str(e):
            db["retry_after"] = time.time() + 3600
            with open(db_path, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            print("🛑 Квота 429. Пауза на 1 годину.")
        else: print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
