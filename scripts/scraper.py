import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    print("📖 Читання скопійованого тексту з raw_text.txt...")
    try:
        with open('raw_text.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Шукаємо години (напр. 08:00-10:00 або 8-10)
        times = re.findall(r'(\d{1,2}(?::\d{2})?\s?-\s?\d{1,2}(?::\d{2})?)', content)
        
        if times:
            periods = sorted(list(set([t.replace(" ", "").replace(".", ":") for t in times])))
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            day_name = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"][now.weekday()]
            
            result = {
                "update_time": now.strftime("%d.%m %H:%M"),
                "queues": {"6.2": {day_name: periods}}
            }
            
            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ УСПІХ! Графік розпізнано: {periods}")
        else:
            print("❌ У файлі raw_text.txt не знайдено годин відключень.")
            
    except FileNotFoundError:
        print("⚠️ Файл raw_text.txt не знайдено! Створи його і встав туди текст із сайту.")

if __name__ == "__main__":
    main()
