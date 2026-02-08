import os
import json
import requests
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Налаштування нового клієнта Google AI
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
MODEL_ID = "gemini-1.5-flash"

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('a', class_='tgme_widget_message_photo_wrap')
        
        if not messages:
            print("❌ Картинки в каналі не знайдено.")
            return None
            
        last_msg = messages[-1]
        style = last_msg.get('style', '')
        
        if "url('" in style:
            img_url = style.split("url('")[1].split("')")[0]
            print(f"✅ Знайдено посилання на графік: {img_url}")
            return img_url
            
    except Exception as e:
        print(f"❌ Помилка парсингу Telegram: {e}")
    return None

def main():
    img_url = get_image_from_telegram()
    if not img_url:
        return

    # Завантаження картинки
    response = requests.get(img_url)
    img_bytes = response.content
    
    prompt = """
    Це графік відключень світла (ГПВ). Витягни дані таблиці для ВСІХ підчерг (1.1, 1.2 і т.д.).
    Поверни ТІЛЬКИ чистий JSON без жодних пояснень:
    {
        "queues": {
            "1.1": {"понеділок": ["час-час", "час-час"]},
            "1.2": {"понеділок": ["час-час"]}
        }
    }
    """
    
    print("🤖 AI розшифровує графік через новий API...")
    
    try:
        # Виклик через нову бібліотеку google-genai
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                prompt,
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            ]
        )
        
        text_response = response.text.strip()
        
        # Очищення від Markdown ```json ... ```
        if "```json" in text_response:
            text_response = text_response.split("```json")[1].split("```")[0]
        elif "```" in text_response:
            text_response = text_response.split("```")[1]
            
        data = json.loads(text_response.strip())
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
        
        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("🎉 Перемога! Файл database_new.json оновлено.")
        
    except Exception as e:
        print(f"❌ Помилка при запиті до AI: {e}")

if __name__ == "__main__":
    main()
