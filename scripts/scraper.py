import json
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo

def parse_schedule(text):
    # Шукаємо блоки, які починаються з назви черги
    # Це дозволить нам обробляти кожен блок окремо зі своєю датою
    blocks = re.split(r'(\d+)\s*черга\s*\((\d+)\s*підгрупа\)', text, flags=re.IGNORECASE)
    
    results = [] # Список знайдених записів: (день, черга_id, години)
    days_ukr = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]

    # blocks[0] - текст до першої черги
    # Далі йдуть трійки: [номер_черги, номер_підгрупи, текст_блоку]
    for i in range(1, len(blocks), 3):
        q_num = blocks[i]
        sub_num = blocks[i+1]
        q_id = f"{q_num}.{sub_num}"
        block_content = blocks[i+2]
        
        # Шукаємо дату саме в ЦЬОМУ блоці
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', block_content)
        if date_match:
            date_obj = datetime.strptime(date_match.group(1), '%d.%m.%Y')
            day_name = days_ukr[date_obj.weekday()]
            
            # Шукаємо години в цьому блоці
            times = re.findall(r'(\d{1,2}:\d{2})', block_content)
            if times:
                clean_periods = [f"{times[j]}-{times[j+1]}" for j in range(0, len(times) - 1, 2)]
                results.append((day_name, q_id, clean_periods))
            
    return results

def main():
    try:
        filename = 'database_v2.json'
        # Завантажуємо існуючий JSON, щоб не стерти дані за інші дні/черги
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                db = json.load(f)
        else:
            db = {"update_time": "", "queues": {}}

        with open('database.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_entries = parse_schedule(content)
        
        if parsed_entries:
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            db["update_time"] = now.strftime("%d.%m %H:%M")
            
            for day_name, q_id, periods in parsed_entries:
                if q_id not in db["queues"]:
                    db["queues"][q_id] = {}
                # Оновлюємо конкретний день для конкретної черги
                db["queues"][q_id][day_name] = periods
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Оброблено {len(parsed_entries)} записів.")
        else:
            print("❌ Не знайдено жодних даних у потрібному форматі.")
            
    except Exception as e:
        print(f"⚠️ Помилка: {e}")

if __name__ == "__main__":
    main()
