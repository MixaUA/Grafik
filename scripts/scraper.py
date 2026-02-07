import requests
from bs4 import BeautifulSoup
import json
import datetime
import time
import random
import os
from zoneinfo import ZoneInfo

TZ_KYIV = ZoneInfo("Europe/Kiev")
MONTHS_UA = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
DAYS_UA = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]

# Створюємо сесію для збереження Cookies (це важливо для обходу захисту)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://sumy.energy-ua.info/',
    'Connection': 'keep-alive'
})

def parse_queue_page(q_id):
    url = f"https://sumy.energy-ua.info/cherga/{q_id.replace('.', '-')}"
    data = {}
    try:
        # Робимо запит через сесію
        response = session.get(url, timeout=20)
        
        # Якщо все одно 403, пробуємо зайти спочатку на головну
        if response.status_code == 403:
            session.get("https://sumy.energy-ua.info/")
            time.sleep(2)
            response = session.get(url, timeout=20)
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Пошук дати (залишаємо як було, бо логіка вірна)
        date_elem = soup.find('div', string=lambda t: t and any(c.isdigit() for c in t) and '.' in t)
        current_page_date = None
        if date_elem:
            d_str = "".join(filter(lambda c: c in "0123456789.", date_elem.get_text()))
            try:
                current_page_date = datetime.datetime.strptime(d_str, "%d.%m.%Y").date()
            except:
                current_page_date = datetime.datetime.now(TZ_KYIV).date()

        # Пошук графіку (як на скріншоті 1)
        headers = soup.find_all(['h2', 'h3', 'div'])
        for h in headers:
            txt = h.get_text().lower()
            if "періоди відключень" in txt:
                ul = h.find_next('ul')
                if ul:
                    periods = []
                    for li in ul.find_all('li'):
                        l_txt = li.get_text()
                        if "з " in l_txt and " до " in l_txt:
                            # 20:00-00:00 -> 20:00-24:00
                            clean = l_txt.replace("з ", "").replace(" до ", "-").split(",")[0].strip()
                            clean = clean.replace("-00:00", "-24:00")
                            periods.append(clean)
                    
                    if current_page_date:
                        day_idx = current_page_date.weekday()
                        if "завтра" in txt:
                            day_idx = (day_idx + 1) % 7
                        data[DAYS_UA[day_idx]] = periods
                        
    except Exception as e:
        print(f"⚠️ Помилка черги {q_id}: {e}")
    return data

def main():
    now = datetime.datetime.now(TZ_KYIV)
    queues = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]
    
    update_time = f"{now.day} {MONTHS_UA[now.month-1]} о {now.strftime('%H:%M')}"
    
    result = {
        "update_time": update_time,
        "queues": {q: {d: [] for d in DAYS_UA} for q in queues}
    }

    # Спершу "прогріваємо" сесію головною сторінкою
    try:
        session.get("https://sumy.energy-ua.info/")
    except:
        pass

    for q in queues:
        print(f"Обробка черги {q}...")
        parsed = parse_queue_page(q)
        for day, p in parsed.items():
            result["queues"][q][day] = p
        
        # Випадкова пауза від 2 до 5 секунд, щоб не здаватися ботом
        time.sleep(random.uniform(2, 5))

    with open('database_v2.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("✨ Все успішно оновлено!")

if __name__ == "__main__":
    main()
