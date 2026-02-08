import os
import json
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Стабільне налаштування Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
# Використовуємо стабільну версію моделі
model = genai.GenerativeModel('gemini-1.5-flash')

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Отримуємо всі блоки повідомлень
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        # Сьогоднішня дата для перевірки (наприклад, "09.02" або "9 лютого")
        today = datetime.now(ZoneInfo("Europe/Kiev"))
        date_str = today.strftime("%d.%m") 
        
        print(f"🔎 Шукаю графік за ключовими словами та датою: {date_str}")

        # Перевіряємо повідомлення з кінця (найновіші)
        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            if not text_area:
                continue
                
            text = text_area.get_text().lower()
            
            # Критерії пошуку: наявність "гпв" або "графік" ТА сьогоднішньої дати
            if ("гпв" in text or "графік" in text) and (date_str in text or "лютого" in text):
                photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
                if photo_wrap:
                    style = photo_wrap.get('style', '')
                    if "url('" in style:
                        img_url = style.split("url('")[1].split("')")[0]
                        print(f"✅ Знайдено актуальний графік! Текст: {text[:50]}...")
                        return img_url
        
        print("⚠️ Актуального графіка з ключовими словами сьогодні ще не було.")
        return None
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
    return None

def main():
    img_url = get_image_from_telegram()
    if not img_url:
        return

    # Завантаження картинки
    response = requests.get(img_url)
    img_data = [{"mime_type": "image/jpeg", "data": response.content}]
    
    prompt = """
    Це графік ГПВ. Витягни дані таблиці для всіх підчерг (1.1 - 6.2).
    Поверни ТІЛЬКИ чистий JSON без пояснень:
    {
        "queues": {
            "1.1": {"понеділок": ["час-час", "час-час"]},
            ...
        }
    }
    Якщо в таблиці є жовті/білі зони, вказуй лише ті інтервали, де світла НЕМАЄ.
    """
    
    print("🤖 AI розшифровує картинку...")
    
    try:
        # Використовуємо стандартний метод генерації
        result = model.generate_content([prompt, img_data[0]])
        
        text_response = result.text.strip()
        if "```json" in text_response:
            text_response = text_response.split("```json")[1].split("```")[0]
        elif "```" in text_response:
            text_response = text_response.split("```")[1]
            
        data = json.loads(text_response.strip())
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
        
        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("🎉 Базу успішно оновлено актуальним графіком!")
        
    except Exception as e:
        print(f"❌ Помилка AI: {e}")

if __name__ == "__main__":
    main()
