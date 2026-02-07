import json
import re
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
                    # Створюємо повну структуру днями, як на скріншоті
                    queues_data[q_id] = {day: [] for day in days_ukr}
                
                queues_data[q_id][day_name] = clean_periods
            
    return queues_data

def main():
    try:
        now = datetime.now(ZoneInfo("Europe/Kiev"))
        with open('database.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_queues = parse_schedule(content)
        
        if parsed_queues:
            # Формуємо JSON з нуля (повний перезапис)
            result = {
                "update_time": now.strftime("%d.%m %H:%M"),
                "queues": parsed_queues
            }
            
            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ ПЕРЕЗАПИСАНО: Структура для {len(parsed_queues)} черг готова.")
        else:
            print("⚠️ Дані не знайдено.")
            
    except Exception as e:
        print(f"❌ ПОМИЛКА: {e}")

if __name__ == "__main__":
    main()
