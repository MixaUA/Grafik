import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    print(f"📡 Пряме підключення до сервера даних...")
    
    # Використовуємо технічну адресу, яку зазвичай не блокують
    # Ми імітуємо запит мобільного додатка
    url = "https://sumy.energy-ua.info/cherga/6-2"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    try:
        # Спробуємо отримати дані напряму через телефон (без моста Google)
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 403:
            print("🛑 Прямий доступ заблоковано. Пробую через резервний шлюз...")
            # Якщо знову 403, використовуємо твій міст, але з покращеною логікою
            response = requests.get(f"https://script.google.com/macros/s/AKfycbx4H1kE5uzLmpCvwVjafysU38c4ibFQ5MDhZQbwCeZNhiaKdR44HIC1qwf29ftG37CLFQ/exec", timeout=30)

        content = response.text
        import re
        # Шукаємо години у форматі 00:00-00:00 або 00-00
        found = re.findall(r'(\d{1,2}[:\.]\d{2}\s?-\s?\d{1,2}[:\.]\d{2})', content)
        
        if not found:
            # Спробуємо знайти простіший формат годин (напр. 8-10)
            found = re.findall(r'\d{1,2}\s?-\s?\d{1,2}', content)

        if found:
            # Очищаємо від дублікатів та сортуємо
            periods = sorted(list(set([p.replace(" ", "").replace(".", ":") for p in found])))
            
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            update_time = now.strftime("%d.%m о %H:%M")
            day_name = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"][now.weekday()]

            result = {
                "update_time": update_time,
                "queues": { "6.2": { day_name: periods } }
            }

            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ ПЕРЕМОГА! Графік знайдено: {', '.join(periods)}")
        else:
            print("❌ Дані на сторінці все ще зашифровані захистом. Потрібен інший метод.")
            
    except Exception as e:
        print(f"⚠️ Помилка: {e}")

if __name__ == "__main__":
    main()
