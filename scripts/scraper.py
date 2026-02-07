import json
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo

def parse_schedule(text):
    queues_data = {}
    # 1. Шукаємо дату в тексті (наприклад, 08.02.2026)
    date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)
    if not date_match:
        return None, None
    
    target_date = datetime.strptime(date_match.group(1), '%d.%m.%Y')
    days_ukr = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
    day_name = days_ukr[target_date.weekday()]

    # 2. Розбиваємо на блоки по чергах
    blocks = re.split(r'(\d+)\s*черга\s*\((\d+)\s*підгрупа\)', text, flags=re.IGNORECASE)
    
    for i in range(1, len(blocks), 3):
        q_id = f"{blocks[i]}.{blocks[i+1]}"
        q_text = blocks[i+2]
        times = re.findall(r'(\d{1,2}:\d{2})', q_text)
        
        if times:
            clean_periods = [f"{times[j]}-{times[j+1]}" for j in range(0, len(times) - 1, 2)]
            queues_data[q_id] = clean_periods
            
    return day_name, queues_data

def main():
    try:
        filename = 'database_v2.json'
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                db = json.load(f)
        else:
            db = {"update_time": "", "queues": {}}

        with open('database.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        day_name, parsed_queues = parse_schedule(content)
        
        if day_name and parsed_queues:
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            db["update_time"] = now.strftime("%d.%m %H:%M")
            
            for q_id, periods in parsed_queues.items():
                if q_id not in db["queues"]:
                    db["queues"][q_id] = {}
                # Записуємо дані саме в той день, який знайшли в тексті
                db["queues"][q_id][day_name] = periods
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Успішно оновлено день: {day_name}")
        else:
            print("❌ Не знайдено дату (00.00.0000) або черги у файлі.")
            
    except Exception as e:
        print(f"⚠️ Помилка: {e}")

if __name__ == "__main__":
    main()
