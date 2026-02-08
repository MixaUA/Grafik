import os
import json
import requests
import re
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    if not msg_data: return

    db_path = 'database_new.json'
    db = {}
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            try: db = json.load(f)
            except: db = {}

    if db.get("last_processed_url") == msg_data["url"] and db.get("last_processed_text") == msg_data["text"]:
        print(f"☕ Gemini НЕ запускається: цей графік вже оброблено.")
        return

    print(f"🤖 Gemini ЗАПУСКАЄТЬСЯ: аналіз оновлень...")

    img_data = requests.get(msg_data["url"]).content
    model_name = 'gemini-2.5-flash'
    
    prompt = """
    Це таблиця ГПВ. Визнач дату (напр. 09.02.2026) та день тижня.
    Витягни інтервали для підчерг 1.1-6.2.
    Поверни ТІЛЬКИ JSON:
    {
      "date": "09.02.2026",
      "day_of_week": "понеділок",
      "queues": { "1.1": ["00:00-02:00", ...], ... }
    }
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': img_data}])
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            res = json.loads(json_match.group())
            new_date = res['date']
            new_day = res['day_of_week'].lower()

            kyiv_now = datetime.now(ZoneInfo("Europe/Kiev"))
            # Визначаємо назви днів для сьогодні та завтра українською
            ua_days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            today_idx = kyiv_now.weekday()
            tomorrow_idx = (today_idx + 1) % 7
            
            today_name = ua_days[today_idx]
            tomorrow_name = ua_days[tomorrow_idx]

            # Якщо структури ще немає — створюємо її
            if "queues" not in db:
                db["queues"] = {q: {d: [] for d in ua_days} for q in res["queues"].keys()}

            # 1. Очищення: для кожної черги затираємо все, що не є сьогодні або завтра
            for q_name in db["queues"]:
                for d_name in ua_days:
                    if d_name != today_name and d_name != tomorrow_name:
                        db["queues"][q_name][d_name] = []

            # 2. Оновлення: записуємо свіжі дані від AI
            for q_name, q_intervals in res["queues"].items():
                if q_name in db["queues"]:
                    db["queues"][q_name][new_day] = q_intervals

            output = {
                "update_time": f"{new_date[:5]} {kyiv_now.strftime('%H:%M')}",
                "queues": db["queues"],
                "last_processed_url": msg_data["url"],
                "last_processed_text": msg_data["text"]
            }

            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"🎉 Успішно! Збережено день: {new_day}. Старі дні (крім сьогодні/завтра) очищено.")
        else:
            print("❌ AI повернув не JSON.")
    except Exception as e:
        print(f"❌ Помилка AI: {e}")

if __name__ == "__main__":
    main()
