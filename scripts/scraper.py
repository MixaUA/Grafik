import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Твій особистий міст через Google
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbx4H1kE5uzLmpCvwVjafysU38c4ibFQ5MDhZQbwCeZNhiaKdR44HIC1qwf29ftG37CLFQ/exec"

def main():
    print(f"📡 Отримання даних через Google Bridge...")
    try:
        response = requests.get(BRIDGE_URL, timeout=30)
        if response.status_code != 200:
            print(f"❌ Помилка моста: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо періоди відключень у списку <ul>
        periods = []
        ul_element = soup.find('ul')
        if ul_element:
            for li in ul_element.find_all('li'):
                txt = li.get_text().strip()
                # Очищаємо текст (напр., "з 08:00 до 10:00" -> "08:00-10:00")
                if "з " in txt and " до " in txt:
                    clean = txt.replace("з ", "").replace(" до ", "-").split(",")[0].strip()
                    periods.append(clean)

        if periods:
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            update_time = now.strftime("%d.%m о %H:%M")
            # Визначаємо день тижня українською
            days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            day_name = days[now.weekday()]

            # Формуємо структуру JSON для черги 6.2
            result = {
                "update_time": update_time,
                "queues": {
                    "6.2": {
                        day_name: periods
                    }
                }
            }

            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Графік оновлено! Знайдено періодів: {len(periods)}")
            print(f"🕒 Час оновлення: {update_time}")
        else:
            print("❓ Графік не знайдено на сторінці через Google Bridge.")

    except Exception as e:
        print(f"⚠️ Помилка: {e}")

if __name__ == "__main__":
    main()
