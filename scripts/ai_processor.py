import os
import json
import requests
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

# Налаштування Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_image_url(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        # Чекаємо, поки картинки з'являться в DOM
        page.wait_for_load_state("networkidle")
        
        imgs = page.query_selector_all("img")
        target_src = None
        for img in imgs:
            src = img.get_attribute("src") or img.get_attribute("data-src")
            alt = img.get_attribute("alt") or ""
            # Шукаємо за ключовими словами
            if src and ("ГПВ" in alt or "графік" in alt.lower() or "люто" in alt.lower() or "02.2026" in src):
                target_src = src if src.startswith('http') else f"https://suspilne.media{src}"
                break
        
        browser.close()
        return target_src

def main():
    url = "https://suspilne.media/sumy/1228481-grafiki-vidklucen-svitla-u-sumskij-oblasti-v-lutomu/"
    img_src = get_image_url(url)
    
    if not img_src:
        print("❌ Графік не знайдено!")
        return
    
    print(f"📸 Знайдено графік: {img_src}")
    response = requests.get(img_src)
    img_bytes = BytesIO(response.content)

    prompt = """
    Це графік відключень світла (ГПВ). Витягни дані таблиці для всіх черг.
    Поверни ТІЛЬКИ чистий JSON без тексту:
    {
        "queues": {
            "1.1": {"понеділок": ["00:00-02:00", "04:00-08:00"]},
            ...
        }
    }
    """
    
    result = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_bytes.getvalue()}])
    
    # Чистимо JSON
    clean_json = result.text.replace('```json', '').replace('```', '').strip()
    data = json.loads(clean_json)
    data["update_time"] = datetime.now(ZoneInfo("Europe/Kiev")).strftime("%d.%m %H:%M")
    
    with open('database_new.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ Дані збережено в database_new.json")

if __name__ == "__main__":
    main()
