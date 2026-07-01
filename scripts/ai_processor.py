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

def check_text_keywords(text):
    """Перевіряє наявність ключових слів з урахуванням різних закінчень (розумний пошук)"""
    if not text:
        return False
    text_lower = text.lower()
    
    # Шаблони для пошуку за сенсом (ігноруючи відмінки та закінчення)
    patterns = [
        r"сумиобленерго",
        r"аварійн.*відключен",
        r"спеціальн.*графік.*аварійн.*відключен",
        r"пошкоджен.*енергосист",
        r"обленерго",
        r"відсутн.*електропостач",
        r"робот.*електромереж"
    ]
    
    return any(re.search(p, text_lower) for p in patterns)

def extract_data_from_msg(msg):
    """Витягує текст, URL фото та URL самого повідомлення Telegram. Відео — ігнорує."""
    text_area = msg.find('div', class_='tgme_widget_message_text')
    photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
    link_area = msg.find('a', class_='tgme_widget_message_date')
    
    # ПЕРЕВІРКА НА ВІДЕО: якщо всередині повідомлення є відео, медіа не чіпаємо
    is_video = msg.find('video') is not None or msg.find('div', class_='tgme_widget_message_video_wrap') is not None
    
    msg_url = link_area.get('href') if link_area else None
    text = text_area.get_text().strip() if text_area else ""
    img_url = None

    # Завантажуємо картинку тільки якщо це не відео
    if photo_wrap and not is_video:
        style = photo_wrap.get('style', '')
        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
        if match:
            img_url = match.group(1)
            if img_url.startswith('//'): img_url = 'https:' + img_url

    return {"url": img_url, "text": text, "msg_url": msg_url}

def get_latest_messages():
    """Збирає останні повідомлення з каналу для аналізу новин та графіків"""
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо всі повідомлення в стрічці
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        extracted_msgs = []
        for msg in messages:
            if 'tgme_widget_message_user_not_supported' in msg.get('class', []):
                continue
            data = extract_data_from_msg(msg)
            if data and (data["text"] or data["url"]):
                extracted_msgs.append(data)
        return extracted_msgs
    except Exception: return []

def send_to_telegram(text, img_url=None):
    """Відправляє текстову новину або новину з фото в телеграм канал"""
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("⚠️ Не знайдено TELEGRAM_TOKEN або TELEGRAM_CHAT_ID в оточенні.")
        return

    # Обов'язкове додавання джерела без переходу в самий кінець повідомлення
    full_text = f"{text}\n\nДжерело: Суспільне Суми"

    try:
        if img_url:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            payload = {'chat_id': chat_id, 'caption': full_text}
            img_data = requests.get(img_url, timeout=15).content
            files = {'photo': ('image.jpg', img_data, 'image/jpeg')}
            response = requests.post(url, data=payload, files=files, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {'chat_id': chat_id, 'text': full_text}
            response = requests.post(url, json=payload, timeout=15)

        if not response.ok:
            print(f"⚠️ Telegram помилка відправки новини: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"❌ Помилка під час відправки в Telegram: {e}")

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

    all_msgs = get_latest_messages()
    if not all_msgs:
        print("☕ Не вдалося отримати дописи з каналу.")
        return

    # ============================================================
    # БЛОК 1: ПЕРЕВІРКА ОПЕРАТИВНИХ НОВИН (ПЕРЕПОСТ ПО КЛЮЧАХ)
    # ============================================================
    latest_news = all_msgs[-1] if all_msgs else None
    
    if latest_news and latest_news["msg_url"] != db.get("last_processed_news_url"):
        if check_text_keywords(latest_news["text"]):
            print(f"📰 Знайдено важливу новину про енергетику! Пересилаю...")
            send_to_telegram(latest_news["text"], latest_news["url"])
            
            # Безпечно оновлюємо мітку новин без зачіпання логіки графіків
            db["last_processed_news_url"] = latest_news["msg_url"]
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)

    # ============================================================
    # БЛОК 2: СТАНДАРТНА ЛОГІКА ПОШУКУ ТА ОБРОБКИ ГРАФІКІВ (БЕЗ ЗМІН)
    # ============================================================
    msg_data = None
    for msg in reversed(all_msgs):
        if msg["text"] and any(word in msg["text"].lower() for word in ["гпв", "графік", "черги"]):
            if msg["url"]: # обов'язково з картинкою графіку для ШІ
                msg_data = msg
                break

    if not msg_data or db.get("last_processed_url") == msg_data["url"]:
        print("☕ Змін у графіках немає.")
        return

    try:
        img_data = requests.get(msg_data["url"]).content
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
            
            raw_date = res.get('date', kyiv_now.strftime("%d.%m.%Y"))
            try:
                date_obj = datetime.strptime(raw_date, "%d.%m.%Y").replace(tzinfo=kyiv_tz)
                target_day = ua_days[date_obj.weekday()]
            except:
                target_day = today_name
            
            all_q_names = [f"{i}.{j}" for i in range(1, 7) for j in range(1, 3)]
            new_queues = {q: {d: [] for d in ua_days} for q in all_q_names}
            
            if "queues" in db:
                for q in all_q_names:
                    for d in [today_name, tomorrow_name]:
                        if d in db["queues"][q]:
                            new_queues[q][d] = db["queues"][q][d]

            for q in all_q_names:
                if q in source and source[q]:
                    new_queues[q][target_day] = source[q]

            update_day_formatted = get_ua_date(kyiv_now.strftime("%d.%m.%Y"))
            
            db["update_time"] = f"{update_day_formatted} {kyiv_now.strftime('%H:%M')}"
            db["queues"] = new_queues
            db["last_processed_url"] = msg_data["url"]
            db["last_processed_text"] = msg_data["text"]

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            print(f"🎉 Графік на {raw_date} ({target_day}) оновлено в базі!")

    except Exception as e:
        if "429" in str(e):
            db["retry_after"] = time.time() + 3600
            with open(db_path, 'w', encoding='utf-8') as f: json.dump(db, f, ensure_ascii=False)
            print("🛑 Квота 429. Пауза на 1 годину.")
        else: print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
