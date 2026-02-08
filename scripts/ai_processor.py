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
model = genai.GenerativeModel('gemini-1.5-flash')

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        last_photo_url = None
        
        print("🔎 Пошук графіка за розширеними фільтрами...")

        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
            
            if not photo_wrap:
                continue
                
            # Витягуємо URL картинки через Regex (надійно)
            style = photo_wrap.get('style', '')
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if not match:
                continue
            
            current_img_url = match.group(1)
            if current_img_url.startswith('//'):
                current_img_url = 'https:' + current_img_url
            
            # Зберігаємо як fallback (найсвіжіше фото в каналі)
            if not last_photo_url:
                last_photo_url = current_img_url

            # Якщо є текст — перевіряємо ключові слова
            if text_area:
                text = text_area.get_text().lower()
                keywords = ["гпв", "графік", "черги", "відключень", "лютого", "завтра"]
                
                # Якщо знайшли ключові слова — це 100% наш графік
                if any(word in text for word in keywords):
                    print(f"✅ Знайдено цільовий графік! Текст: {text[:40]}...")
                    return current_img_url

        # Якщо пройшли всі повідомлення і не знайшли точного збігу — беремо останнє фото
        if last_photo_url:
            print("⚠️ Точного збігу не знайдено. Fallback: беремо останнє фото з каналу.")
            return last_photo_url
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
    return None

def main():
    img_url = get_image_from_telegram()
    if not img_url:
        print("🛑 Картинку не знайдено взагалі.")
        return

    img_data = requests.get(img_url).content
    
    # Промпт адаптований під добовий цикл (як на твоїх скрінах)
    prompt = """
    Це графік ГПВ Сумщина. Таблиця з підчергами 1.1–6.2 та часовими діапазонами.
    Жовті клітинки — це вимкнення світла.
    Витягни ТІЛЬКИ чистий JSON без пояснень:
    {
      "queues": {
        "1.1": ["00:00-02:00", "12:00-16:00"],
        "1.2": ["02:00-06:00"]
      }
    }
    """
    
    try:
        response = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': img_data}
        ])
        
        # Очищення JSON
        raw_text = response.text
        json_str = raw_text.split("```json")[-1].split("```")[0].strip() if "```" in raw_text else raw_text.strip()
        
        data = json.loads(json_str)
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
        
        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("🎉 Базу успішно оновлено!")
        
    except Exception as e:
        print(f"❌ Помилка AI або JSON: {e}")

if __name__ == "__main__":
    main()
