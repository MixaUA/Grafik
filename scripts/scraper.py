import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# Твій перевірений міст
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbx4H1kE5uzLmpCvwVjafysU38c4ibFQ5MDhZQbwCeZNhiaKdR44HIC1qwf29ftG37CLFQ/exec"

def main():
    print(f"📡 Отримання даних через Google Bridge...")
    try:
        response = requests.get(BRIDGE_URL, timeout=30)
        if response.status_code != 200:
            print(f"❌ Помилка моста: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        periods = []

        # ШУКАЄМО ГРАФІК: Варіант 1 (список <ul>)
        ul_element = soup.find('ul')
        if ul_element:
            for li in ul_element.find_all('li'):
                txt = li.get_text().strip()
                if any(char.isdigit() for char in txt): # Перевіряємо, чи є цифри (години)
                    clean = txt.replace("з ", "").replace(" до ", "-").split(",")[0].replace("год.", "").strip()
                    if "-" in clean:
                        periods.append(clean)

        # Якщо не знайшли в списку, шукаємо просто в тексті (Варіант 2)
        if not periods:
            all_text = soup.get_text()
            print("🔍 Пошук годин у тексті сторінки...")
            import re
            # Шукаємо шаблони типу 08:00-10:00 або 08-10
            found = re.findall(r'\d{1,2}[:\.]?\d{0,2}\s?-\s?\d{1,2}[:\.]?\d{0,2}', all_text)
            periods = [p.replace(" ", "") for p in found]

        if periods:
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            update_time = now.strftime("%d.%m о %H:%M")
            days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            day_name = days[now.weekday()]

            result = {
                "update_time": update_time,
                "queues": {
                    "6.2": { day_name: periods }
                }
            }

            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ ПЕРЕМОГА! Графік оновлено: {', '.join(periods)}")
        else:
            print("❓ Годин відключень не знайдено. Перевір посилання в Google Script.")
            # Виведемо шматочок тексту для діагностики
            print(f"Уривок тексту: {soup.get_text()[:200]}...")

    except Exception as e:
        print(f"⚠️ Помилка: {e}")

if __name__ == "__main__":
    main()
