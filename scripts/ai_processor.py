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
    # Розширені заголовки, щоб імітувати реальний браузер
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        # Зберігаємо сторінку для діагностики, якщо щось піде не так
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Спробуємо знайти всі картинки на сторінці взагалі
        images = soup.find_all('img')
        print(f"Знайдено всього картинок на сторінці: {len(images)}")
        
        for img in images:
            # Перевіряємо різні атрибути, де може ховатися посилання
            src = img.get('src') or img.get('data-src') or img.get('srcset')
            
            if src:
                # Очищуємо посилання, якщо це srcset
                src = src.split(' ')[0]
                
                # Шукаємо за ключовими словами в назві файлу
                if any(word in src.lower() for word in ['grafik', 'gvp', 'svitlo', '1200x']):
                    if not src.startswith('http'):
                        src = "https://suspilne.media" + src
                    return src
                    
    except Exception as e:
        print(f"Помилка при парсингу: {e}")
    return None

def main():
    try:
        print("🔍 Починаю пошук картинки...")
        img_url = get_latest_image_url()
        
        if not img_url:
            print("❌ Картинку не знайдено. HTML збережено в debug_page.html")
            return

        print(f"📸 Знайдено URL: {img_url}")
        img_response = requests.get(img_url, timeout=20)
        
        prompt = """
        Це графік ГПВ (відключень). 
        Витягни дані тільки для 'понеділок' (або актуального дня).
        Поверни JSON: {"queues": {"1.1": {"понеділок": ["час-час"]}}}
        """

        print("🤖 Gemini обробляє...")
        result = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': img_response.content}
        ])

        output = result.text.strip()
        if '```' in output:
            output = output.split('```')[1].replace('json', '').strip()
        
        data = json.loads(output)
        data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")

        with open('database_new.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("✅ Успіх! Перевір database_new.json")

    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
