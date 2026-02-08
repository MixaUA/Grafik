import os
import json
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Налаштування Gemini (фіксуємо стабільну версію)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_image_from_telegram():
    channel_url = "https://t.me/s/suspilnesumy"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(channel_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Отримуємо всі повідомлення
        messages = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        # Визначаємо сьогоднішню дату для фільтра (наприклад, "9 лютого")
        today = datetime.now(ZoneInfo("Europe/Kiev"))
        months = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
        date_filter = f"{today.day} {months[today.month-1]}"
        
        print(f"🔎 Пошук графіка за маркерами: 'ГПВ на', 'черги' та датою '{date_filter}'")

        # Йдемо від нових повідомлень до старих
        for msg in reversed(messages):
            text_area = msg.find('div', class_='tgme_widget_message_text')
            if not text_area:
                continue
                
            text = text_area.get_text().lower()
            
            # Перевірка на ключові слова зі скріншотів
            if "гпв на" in text and date_filter in text:
                photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
                if photo_wrap:
                    style = photo_wrap.get('style', '')
                    if "url('" in style:
                        img_url = style.split("url('")[1].split("')")[0]
                        print(f"✅ Знайдено актуальний графік! Текст: {text[:60]}...")
                        return img_url
        
        print(f"⚠️ Повідомлення з графіком на {date_filter} ще не опубліковано.")
        return None
            
    except Exception as e:
        print(f"❌ Помилка при парсингу Telegram: {e}")
        return None

def main():
    img_url = get_image_from_telegram()
    if not img_url:
        return

    # Завантаження картинки
    img_response = requests.get(img_url)
    img_parts = [{"mime_type": "image/jpeg", "data": img_response.content}]
    
    # Промпт з назвами колонок зі скріншотів
    prompt = """
    Це графік ГПВ (черги вимкнень). На зображенні таблиця з колонками 'Підчерга' та 'Діапазони відключень'.
    Витягни дані для всіх підчерг (1.1 - 6.2).
    Поверни ТІЛЬКИ чистий JSON без пояснень:
    {
        "queues": {
            "1.1": {"понеділок": ["00:00-02:00", "12:00-16:00"]},
            ...
        }
    }
    Важливо: якщо клітинка жовта або з текстом часу — це період ВІДКЛЮЧЕННЯ.
    """
    
    print("🤖 AI розшифровує знайдений графік...")
    
    try:
        # Виклик моделі
        result = model.generate_content([prompt, img_parts[0]])
        
        # Очищення відповіді
        res_text = result.text.strip()
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0]
        elif "```" in res_text:
            res_text = res_text.split("```")[1]
            
        data = json.loads(res_text.strip())
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
        
        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("🎉 Готово! database_new.json оновлено актуальними даними.")
        
    except Exception as e:
        print(f"❌ Помилка AI: {e}")

if __name__ == "__main__":
    main()
