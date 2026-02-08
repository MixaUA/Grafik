import os
import json
import requests
import re
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Налаштування Gemini з примусовим використанням стабільної версії v1
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        last_photo_url = None
        
        print("🔎 Пошук графіка за розширеними фільтрами (включаючи прикріплені)...")

        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
            
            if not photo_wrap:
                continue
                
            # Надійний витяг URL через Regex [за твоєю рекомендацією]
            style = photo_wrap.get('style', '')
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if not match:
                continue
            
            current_img_url = match.group(1)
            if current_img_url.startswith('//'):
                current_img_url = 'https:' + current_img_url
            
            # Зберігаємо як fallback
            if not last_photo_url:
                last_photo_url = current_img_url

            if text_area:
                text = text_area.get_text().lower()
                # Розширений фільтр ключових слів
                keywords = ["гпв на", "гпв", "графік", "черги", "відключень", "9 лютого", "лютого"]
                
                if any(word in text for word in keywords):
                    print(f"✅ Знайдено цільовий графік! Текст: {text[:50]}...")
                    return current_img_url

        if last_photo_url:
            print("⚠️ Fallback: беремо останнє фото з каналу.")
            return last_photo_url
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
    return None

def main():
    img_url = get_image_from_telegram()
    if not img_url:
        return

    img_data = requests.get(img_url).content
    
    # Використовуємо модель через фіксований шлях, щоб уникнути помилки 404
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    
    prompt = """
    Це графік ГПВ Сумщина. Таблиця з підчергами 1.1–6.2. 
    Жовті клітинки — світла немає.
    Поверни ТІЛЬКИ чистий JSON без тексту:
    {
      "queues": {
        "1.1": ["00:00-02:00", "12:00-16:00"],
        "1.2": ["02:00-06:00"]
      }
    }
    """
    
    print("🤖 AI розшифровує графік (через стабільний API)...")
    try:
        # Використовуємо generation_config для стабільності
        response = model.generate_content(
            contents=[
                prompt,
                {'mime_type': 'image/jpeg', 'data': img_data}
            ]
        )
        
        raw_text = response.text
        # Витягуємо JSON навіть якщо AI додав зайве
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
            
            with open('database_new.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("🎉 ПЕРЕМОГА! База оновлена.")
        else:
            print(f"❌ Не вдалося знайти JSON у відповіді: {raw_text}")
            
    except Exception as e:
        print(f"❌ Критична помилка AI: {e}")

if __name__ == "__main__":
    main()
