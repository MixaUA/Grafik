import requests
import re
import json
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    # Цей URL — "чорний хід", який часто забувають закрити щитом
    url = "https://sumy.energy-ua.info/cherga/6-2"
    
    # Імітуємо ПОВНИЙ набір заголовків сучасного браузера
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

    print("🚀 Спроба прориву через мобільну імітацію...")
    
    try:
        # Робимо запит через сесію, щоб зберегти cookies (це обходить Cloudflare у 90% випадків)
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        
        content = response.text
        # Витягуємо ВСІ цифри, схожі на часові інтервали (напр. 08:00-10:00 або 8-10)
        times = re.findall(r'(\d{1,2}(?::\d{2})?\s?-\s?\d{1,2}(?::\d{2})?)', content)
        
        if times:
            periods = sorted(list(set([t.replace(" ", "") for t in times])))
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            day_name = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"][now.weekday()]
            
            result = {
                "update_time": now.strftime("%d.%m %H:%M"),
                "queues": {"6.2": {day_name: periods}}
            }
            
            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ ПЕРЕМОГА! Знайдено часи: {periods}")
        else:
            print("🧱 Сайт віддав порожню сторінку. Cloudflare нас переграв.")
            print(f"Статус: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Помилка: {e}")

if __name__ == "__main__":
    main()
