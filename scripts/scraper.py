import requests
from bs4 import BeautifulSoup
import json
import datetime
import time
import os
from zoneinfo import ZoneInfo

TZ_KYIV = ZoneInfo("Europe/Kiev")
MONTHS_UA = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4, "травня": 5, "червня": 6,
    "липня": 7, "серпня": 8, "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12
}
DAYS_UA = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

def parse_queue_page(q_id):
    url = f"https://sumy.energy-ua.info/cherga/{q_id.replace('.', '-')}"
    data = {}
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Знаходимо всі блоки з графіками
        # Шукаємо заголовки, які містять "сьогодні" або "завтра" + дату
        headers = soup.find_all(['h2', 'h3', 'div'], class_=lambda x: x and ('title' in x or 'header' in x) or True)
        
        for header in headers:
            h_text = header.get_text().lower()
            if "періоди відключень" not in h_text:
                continue
                
            # Визначаємо день (сьогодні/завтра) та дату
            target_date = None
            if "сьогодні" in h_text or (header.find_previous('div', class_='date') and "сьогодні" in header.find_previous('div', class_='date').text.lower()):
                # Спробуємо витягти дату з тексту вище (напр. "07.02.2026")
                date_elem = soup.find('div', string=lambda t: t and any(char.isdigit() for char in t) and '.' in t)
                if date_elem:
                    # Спрощена логіка: беремо дату зі сторінки
                    date_str = "".join(filter(lambda c: c in "0123456789.", date_elem.get_text()))
                    try:
                        target_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                    except:
                        target_date = datetime.datetime.now(TZ_KYIV).date()
            
            # Якщо знайшли список <li> після заголовка
            ul = header.find_next('ul')
            if ul:
                periods = []
                for li in ul.find_all('li'):
                    txt = li.get_text()
                    if "з " in txt and " до " in txt:
                        clean = txt.replace("з ", "").replace(" до ", "-").split(",")[0].strip()
                        periods.append(clean)
                
                if target_date:
                    day_name = DAYS_UA[target_date.weekday()]
                    data[day_name] = periods
                    
    except Exception as e:
        print(f"⚠️ Помилка черги {q_id}: {e}")
    return data

def main():
    now = datetime.datetime.now(TZ_KYIV)
    queues_list = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]
    
    # Ініціалізуємо порожню структуру
    result = {
        "update_time": now.strftime("%-d %B о %H:%M").replace(now.strftime("%B"), list(MONTHS_UA.keys())[now.month-1]),
        "queues": {q: {day: [] for day in DAYS_UA} for q in queues_list}
    }

    for q in queues_list:
        print(f"Обробка черги {q}...")
        parsed_data = parse_queue_page(q)
        for day, periods in parsed_data.items():
            result["queues"][q][day] = periods
        time.sleep(1.5) # Пауза 1.5 сек між запитами

    with open('database_v2.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("✨ Готово: database_v2.json оновлено")

if __name__ == "__main__":
    main()
