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

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        last_photo_url = None
        print("🔎 Пошук останнього графіка в каналі...")

        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
            
            if not photo_wrap: continue
                
            style = photo_wrap.get('style', '')
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if not match: continue
            
            img_url = match.group(1)
            if img_url.startswith('//'): img_url = 'https:' + img_url
            
            if not last_photo_url: last_photo_url = img_url

            if text_area:
                text = text_area.get_text().lower()
                if any(word in text for word in ["гпв", "графік", "черги", "відключень"]):
                    print(f"✅ Знайдено графік за текстом: {text[:40]}...")
                    return img_url

        return last_photo_url
            
    except Exception as e:
        print(f"❌ Помилка парсингу Telegram: {e}")
    return None

def main():
    img_url = get_image_from_telegram()
    if not img_url: return

    img_data = requests.get(img_url).content
    model_name = 'gemini-2.5-flash'
    
    # Максимально жорсткий промпт: просто зчитати текст
    prompt = """
    Це таблиця графіку відключень світла. 
    ЗАВДАННЯ: Для кожної підчерги (1.1, 1.2, 2.1... до 6.2) випиши ВСІ часові інтервали, вказані в її рядку.
    ВСІ прямокутники з часом у таблиці — це періоди ВІДКЛЮЧЕННЯ.

    Поверни ТІЛЬКИ чистий JSON без жодних твоїх коментарів:
    {
      "queues": {
        "1.1": ["00:00-02:00", "04:00-08:00", "10:00-14:00", "16:00-20:00", "22:00-00:00"],
        "1.2": ["02:00-06:00", "08:00-12:00", "14:00-18:00", "20:00-00:00"],
        ...
      }
    }
    Важливо: не пропускай жодного інтервалу. Якщо в рядку підчерги є час — додавай його в список.
    """
    
    print(f"🤖 AI зчитує всі дані через {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': img_data}
        ])
        
        # Витягуємо JSON через Regex
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
            
            with open('database_new.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("🎉 ПЕРЕМОГА! База database_new.json оновлена коректно.")
        else:
            print(f"❌ AI видав не JSON: {response.text}")
            
    except Exception as e:
        print(f"❌ Помилка AI: {e}")

if __name__ == "__main__":
    main()
