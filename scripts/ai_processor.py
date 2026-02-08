import os
import json
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Налаштування Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        # Дати для пошуку: сьогодні та завтра
        tz = ZoneInfo("Europe/Kiev")
        today = datetime.now(tz)
        tomorrow = today + timedelta(days=1)
        months = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
        
        search_dates = [
            f"{today.day} {months[today.month-1]}",
            f"{tomorrow.day} {months[tomorrow.month-1]}"
        ]
        
        print(f"🔎 Шукаю графіки на: {search_dates}")

        # Шукаємо найсвіжіше повідомлення, що підходить під фільтр
        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            if not text_area: continue
            
            text = text_area.get_text().lower()
            
            # Перевірка: має бути "гпв на" ТА одна з дат ТА слово "черги"
            if "гпв на" in text and any(d in text for d in search_dates):
                photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
                if photo_wrap:
                    style = photo_wrap.get('style', '')
                    if "url('" in style:
                        img_url = style.split("url('")[1].split("')")[0]
                        print(f"✅ Знайдено графік! Текст: {text[:50]}...")
                        return img_url
        
        print("⚠️ Актуальних повідомлень з графіком не знайдено.")
        return None
            
    except Exception as e:
        print(f"❌ Помилка парсингу: {e}")
        return None

def main():
    img_url = get_image_from_telegram()
    if not img_url: return

    img_data = requests.get(img_url).content
    
    # Промпт з ключовими словами з твоїх скриншотів
    prompt = """
    Це графік ГПВ (черги вимкнень). На зображенні таблиця 'Підчерга' та 'Діапазони відключень'.
    Витягни дані для всіх підчерг (1.1 - 6.2).
    Поверни ТІЛЬКИ чистий JSON:
    {
        "queues": {
            "1.1": {"понеділок": ["00:00-02:00", "12:00-16:00"]},
            ...
        }
    }
    Жовті клітинки — це вимкнення.
    """
    
    print("🤖 AI розшифровує знайдений графік...")
    try:
        # Використовуємо стабільний виклик (без v1beta)
        result = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_data}])
        
        res_text = result.text.strip()
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0]
        
        data = json.loads(res_text.strip())
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
        
        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("🎉 Базу оновлено!")
        
    except Exception as e:
        print(f"❌ Помилка AI: {e}")

if __name__ == "__main__":
    main()
