import os
import json
import requests
import re
import time
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Використовуємо найновішу модель, яку ми бачили в твоїй панелі
MODEL_NAME = 'gemini-2.5-flash' 
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def get_ua_date(date_str):
    months = {"01":"січня","02":"лютого","03":"березня","04":"квітня","05":"травня","06":"червня","07":"липня","08":"серпня","09":"вересня","10":"жовтня","11":"листопада","12":"грудня"}
    try:
        day, month, _ = date_str.split('.')
        return f"{int(day)} {months.get(month, month)}"
    except: return date_str

def extract_data_from_msg(msg):
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
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Спершу перевіряємо закріплені повідомлення
        pinned_msg = soup.find('div', class_='tgme_widget_message_pinned')
        if pinned_msg:
            data = extract_data_from_msg(pinned_msg)
            if data: return data

        # Якщо в закріпах немає - шукаємо в стрічці
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        for msg in reversed(messages):
            data = extract_data_from_msg(msg)
            if data: return data
        return None
    except Exception: return None

def main():
    db_path = 'database.json'
    db = {}
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    # Захист від 429 (якщо маркер є - чекаємо)
    retry_after = db.get("retry_after")
    if retry_after and time.time() < retry_after:
        print(f"⏳ ЗАХИСТ: До оновлення квот ще {int((retry_after - time.time())/60)} хв.")
        return

    msg_data = get_latest_msg_data()
    if not msg_data: return

    # Економія: не запускаємо Gemini, якщо фото те саме
    if db.get("last_processed_url") == msg_data["url"]:
        print(f"☕ Змін немає. Новий графік ще не опубліковано.")
        return

    try:
        img_data = requests.get(msg_data["url"]).content
        prompt = "Це таблиця ГПВ. Визнач дату (DD.MM.YYYY). Витягни інтервали для підчерг 1.1-6.2. Поверни JSON."
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[types.Part.from_text(text=prompt), types.Part.from_bytes(data=img_data, mime_type='image/jpeg')]
        )
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            res = json.loads(json_match.group())
            ua_days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            kyiv_now = datetime.now(ZoneInfo("Europe/Kiev"))
            all_q_names = [f"{i}.{j}" for i in range(1, 7) for j in range(1, 3)]
            
            if "queues" not in db: db["queues"] = {q: {d: [] for d in ua_days} for q in all_q_names}
            
            target_day = res.get('day_of_week', ua_days[kyiv_now.weekday()]).lower()
            queues_source = res.get('queues', res)
            
            for q_name in all_q_names:
                if q_name in queues_source:
                    db["queues"][q_name][target_day] = queues_source[q_name]

            display_date = get_ua_date(res.get('date', kyiv_now.strftime("%d.%m.%Y")))
            
            output = {
                "update_time": f"{display_date} {kyiv_now.strftime('%H:%M')}",
                "queues": db["queues"],
                "last_processed_url": msg_data["url"],
                "last_processed_text": msg_data["text"]
            }
            # Якщо успішно - видаляємо маркер захисту
            if "retry_after" in output: del output["retry_after"]

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"🎉 Новий графік на {display_date} оброблено!")

    except Exception as e:
        if "429" in str(e):
            db["retry_after"] = time.time() + 3600
            with open(db_path, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            print("🛑 КВОТА 429. Пауза на 1 годину.")
        else: print(f"❌ ПОМИЛКА: {e}")

if __name__ == "__main__":
    main()
