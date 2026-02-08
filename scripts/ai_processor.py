import os
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Налаштування
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_image_url():
    url = "https://suspilne.media/sumy/1228481-grafiki-vidklucen-svitla-u-sumskij-oblasti-v-lutomu/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        img = soup.find('article').find('img')
        if img and 'src' in img.attrs:
            return img['src']
    except Exception as e:
        print(f"Помилка при пошуку картинки: {e}")
    return None

def main():
    try:
        img_url = get_latest_image_url()
        if not img_url:
            print("Картинку не знайдено.")
            return

        print(f"Отримано URL: {img_url}")
        response = requests.get(img_url)
        
        prompt = """
        Це графік відключень світла. Витягни дані з таблиці.
        Поверни дані ТІЛЬКИ у форматі JSON:
        {
          "queues": {
            "1.1": {"понеділок": ["час-час", "час-час"]},
            ...
          }
        }
        Використовуй формат 24h. Тільки чистий JSON без тексту навколо.
        """

        result = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': response.content}
        ])

        # Очищення та збереження
        raw_text = result.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")

        # Тимчасовий файл для перевірки
        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("✅ Файл database_new.json створено успішно!")

    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
