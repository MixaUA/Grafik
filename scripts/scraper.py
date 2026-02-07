import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def parse_schedule(text):
    # Словник для результатів
    queues_data = {}
    
    # Шукаємо блоки тексту для кожної черги (наприклад, "Черга 6.1" або "Група 6.1")
    # Цей вираз шукає номер черги і весь текст після нього до наступної черги
    blocks = re.split(r'(?:Черга|Група|Групи)\s*(\d+\.\d+)', text, flags=re.IGNORECASE)
    
    # blocks[0] - це текст до першої згадки черги
    # Далі йдуть пари: [номер_черги, текст_з_годинами]
    for i in range(1, len(blocks), 2):
        q_name = blocks[i].strip()
        q_text = blocks[i+1]
        
        # Шукаємо години формату 00:00-00:00 або 00-00
        times = re.findall(r'(\d{1,2}(?::\d{2})?[\s\-\–до]+?\d{1,2}(?::\d{2})?)', q_text)
        
        if times:
            # Чистимо формати (замінюємо "до", пробіли тощо на чисте "-")
            clean_periods = []
            for t in times:
                clean_t = re.sub(r'\s*[\-\–до]+\s*', '-', t).strip()
                clean_periods.append(clean_t)
            
            queues_data[q_name] = sorted(list(set(clean_periods)))
            
    return queues_data

def main():
    print("📖 Читання тексту з database.txt...")
    try:
        with open('database.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_queues = parse_schedule(content)
        
        if parsed_queues:
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            day_name = days[now.weekday()]
            
            # Формуємо структуру саме для database_v2.json
            result = {
                "update_time": now.strftime("%d.%m %H:%M"),
                "queues": {}
            }
            
            for q_id, periods in parsed_queues.items():
                result["queues"][q_id] = {day_name: periods}
            
            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ УСПІХ! Оновлено черги: {list(parsed_queues.keys())}")
        else:
            print("❌ Не вдалося знайти черги або години у database.txt")
            
    except Exception as e:
        print(f"⚠️ Помилка: {e}")

if __name__ == "__main__":
    main()
