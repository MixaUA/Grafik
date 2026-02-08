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
        print("🔎 Пошук актуального графіка...")

        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
            
            if not photo_wrap: continue
                
            # Regex для URL (твоя рекомендація)
            style = photo_wrap.get('style', '')
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if not match: continue
            
            current_img_url = match.group(1)
            if current_img_url.startswith('//'): current_img_url = 'https:' + current_img_url
            
            if not last_photo_url: last_photo_url = current_img_url

            if text_area:
                text = text_area.get_text().lower()
                # Широкий набір ключів для 100% знаходження
                if any(word in text for word in ["гпв", "графік", "черги", "відключень", "лютого"]):
                    print(f"✅ Знайдено цільовий пост! Текст: {text[:50]}...")
                    return current_img_url

        return last_photo_url
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
    return None

def main():
    img_url = get_image_from_telegram()
    if not img_url: return

    img_data = requests.get(img_url).content
    
    # Використовуємо Gemini 2.5 Flash (рекомендовано для 2026 року)
    model_name = 'gemini-2.5-flash'
    print(f"🤖 AI розшифровує графік через {model_name}...")
    
    try:
        model = genai.GenerativeModel(model_name)
        
        prompt = """
        Це актуальний графік ГПВ Сумської області. Таблиця містить підчерги 1.1–6.2.
        Жовті/заповнені клітинки означають відсутність світла.
        Поверни ТІЛЬКИ JSON:
        {
          "queues": {
            "1.1": ["00:00-02:00", "12:00-16:00"],
            "1.2": ["02:00-06:00"]
          }
        }
        """
        
        response = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': img_data}
        ])
        
        # Надійний витяг JSON через Regex
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
            
            with open('database_new.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("🎉 ПЕРЕМОГА! База database_new.json оновлена.")
        else:
            print(f"❌ Помилка: AI не повернув JSON. Відповідь: {response.text}")
            
    except Exception as e:
        print(f"❌ Критична помилка AI: {e}")

if __name__ == "__main__":
    main()
