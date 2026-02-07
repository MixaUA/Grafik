import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def parse_schedule(text):
    queues_data = {}
    # Шукаємо блоки черг. Враховуємо, що пробілів може не бути
    blocks = re.split(r'(\d+)\s*черга\s*\((\d+)\s*підгрупа\)', text, flags=re.IGNORECASE)
    
    for i in range(1, len(blocks), 3):
        q_id = f"{blocks[i]}.{blocks[i+1]}"
        q_text = blocks[i+2]
        
        # Шукаємо години. \d{1,2}:\d{2} знайде "02:00", "20:00" тощо навіть всередині тексту "З02:00до06:00"
        times = re.findall(r'(\d{1,2}:\d{2})', q_text)
        
        if times:
            clean_periods = []
            # Беремо години парами: 1-а і 2-а, 3-я і 4-а...
            for j in range(0, len(times) - 1, 2):
                start = times[j]
                end = times[j+1]
                clean_periods.append(f"{start}-{end}")
            
            if clean_periods:
                queues_data[q_id] = clean_periods
            
    return queues_data

def main():
    try:
        with open('database.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_queues = parse_schedule(content)
        
        if parsed_queues:
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            
            # Визначаємо день: шукаємо слово "завтра" у всьому тексті
            if "завтра" in content.lower():
                target_date = now + timedelta(days=1)
                status_msg = "ЗАВТРА"
            else:
                target_date = now
                status_msg = "СЬОГОДНІ"

            days_ukr = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            day_name = days_ukr[target_date.weekday()]
            
            result = {
                "update_time": now.strftime("%d.%m %H:%M"),
                "queues": {}
            }
            
            for q_id, periods in parsed_queues.items():
                result["queues"][q_id] = {day_name: periods}
            
            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ УСПІХ! Графік на {status_msg} ({day_name}) оброблено.")
            print(f"Знайдені черги: {list(parsed_queues.keys())}")
        else:
            print("❌ Не вдалося розпізнати жодної черги. Перевір, чи скопіював ти текст 'X черга (Y підгрупа)'")
            
    except Exception as e:
        print(f"⚠️ Критична помилка: {e}")

if __name__ == "__main__":
    main()
