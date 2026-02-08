import os
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Авторизація
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_latest_image_url():
    url = "https://suspilne.media/sumy/1228481-grafiki-vidklucen-svitla-u-sumskij-oblasti-v-lutomu/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо всі зображення в основному контенті статті
        article = soup.find('article') or soup.find('main')
        if not article:
            return None
            
        images = article.find_all('img')
        for img in images:
            src = img.get('src') or img.get('data-src')
            # Графіки зазвичай великі та мають ключові слова в назві або атрибутах
            if src and ('grafik' in src.lower() or 'gvp' in src.lower() or 'svitlo' in src.lower()):
                if not src.startswith('http'):
                    src = "https://suspilne.media" + src
                return src
        
        # Якщо за назвою не знайшли, беремо просто перше велике зображення
        if images:
            src = images[0].get('src')
            if src and not src.startswith('http'):
                src = "https://suspilne.media" + src
            return src
            
    except Exception as e:
        print(f"Помилка при парсингу сайту: {e}")
    return None

def main():
    try:
        print("🔍 Шукаю актуальну картинку...")
        img_url = get_latest_image_url()
        
        if not img_url:
            print("❌ Картинку на сторінці не знайдено. Перевір структуру сайту.")
            return

        print(f"📸 Знайдено URL: {img_url}")
        img_response = requests.get(img_url, timeout=15)
        
        prompt = """
        Це таблиця графіка відключень електроенергії.
        Витягни дані та сформуй JSON.
        Ключі - це підчерги (наприклад, "1.1", "1.2").
        Значення - масив часових інтервалів для 'понеділок'.
        Поверни ТІЛЬКИ чистий JSON без жодних коментарів.
        """

        print("🤖 Gemini обробляє зображення...")
        result = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': img_response.content}
        ])

        # Чистимо текст від маркерів markdown
        output = result.text.strip()
        if output.startswith('```'):
            output = output.split('```')[1]
            if output.startswith('json'):
                output = output[4:]
        
        data = json.loads(output.strip())
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")

        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("✅ Успішно! Файл database_new.json оновлено.")

    except Exception as e:
        print(f"❌ Критична помилка: {e}")

if __name__ == "__main__":
    main()
