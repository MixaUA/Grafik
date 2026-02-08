import json
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo

def parse_schedule(text):
    # Розбиваємо текст на блоки по чергах
    blocks = re.split(r'(\d+)\s*черга\s*\((\d+)\s*підгрупа\)', text, flags=re.IGNORECASE)
    
    queues_data = {}
    days_ukr = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]

    for i in range(1, len(blocks), 3):
        q_id = f"{blocks[i]}.{blocks[i+1]}"
        block_content = blocks[i+2]
        
        # Шукаємо дату в блоці (наприклад, 08.02.2026)
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', block_content)
        if date_match:
            date_obj = datetime.strptime(date_match.group(1), '%d.%m.%Y')
            day_name = days_ukr[date_obj.weekday()]
            
            # Шукаємо години (00:00)
            times = re.findall(r'(\d{1,2}:\d{2})', block_content)
            if times:
                clean_periods = [f"{times[j]}-{times[j+1]}" for j in range(0, len(times) - 1, 2)]
                
                if q_id not in queues_data:
                    queues_data[q_id] = {day: [] for day in days_ukr}
                
                queues_data[q_id][day_name] = clean_periods
            
    return queues_data

def main():
    # Шлях до файлів (враховуючи, що скрипт в /scripts, а файли в корені)
    input_file = 'database.txt'
    output_file = 'database.json'

    try:
        now = datetime.now(ZoneInfo("Europe/Kiev"))
        months_ukr = {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
            5: "травня", 6: "червня", 7: "липня", 8: "серпня",
            9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        }
        formatted_date = f"{now.day} {months_ukr[now.month]} {now.strftime('%H:%M')}"

        if not os.path.exists(input_file):
            print(f"❌ Файл {input_file} не знайдено.")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            print("⚠️ Файл database.txt порожній. Скасування.")
            return
        
        parsed_queues = parse_schedule(content)
        
        # Перевірка, чи знайшли ми хоч якісь дані
        if parsed_queues and any(v for v in parsed_queues.values()):
            result = {
                "update_time": formatted_date,
                "queues": parsed_queues
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Успішно! Базу оновлено: {formatted_date}")
        else:
            print("⚠️ Парсер не знайшов даних у тексті. database.json не змінено.")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
