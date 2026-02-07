import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    # 1. Читаємо твій текстовий файл, куди ти вставляєш графік
    print("📖 Читання тексту з database.txt...")
    try:
        with open('database.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2. Шукаємо години (наприклад, 08:00-12:00 або 8-12)
        # Регулярний вираз підлаштований під формат, який ми бачили у тебе в таблицях
        times = re.findall(r'(\d{1,2}(?::\d{2})?\s?до\s?\d{1,2}(?::\d{2})?)', content)
        
        if not times:
            # Спробуємо альтернативний формат з тире
            times = re.findall(r'(\d{1,2}(?::\d{2})?\s?-\s?\d{1,2}(?::\d{2})?)', content)

        if times:
            # Очищаємо та сортуємо періоди
            periods = sorted(list(set([t.replace("до", "-").replace(" ", "") for t in times])))
            
            # Визначаємо поточний день
            now = datetime.now(ZoneInfo("Europe/Kiev"))
            days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
            day_name = days[now.weekday()]
            
            # 3. Формуємо структуру для сайту
            result = {
                "update_time": now.strftime("%d.%m %H:%M"),
                "queues": {
                    "6.2": {
                        day_name: periods
                    }
                }
            }
            
            # 4. Записуємо в JSON, який читає твій index.html
            with open('database_v2.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ УСПІХ! Графік оновлено для {day_name}: {periods}")
        else:
            print("❌ У файлі database.txt не знайдено часових інтервалів.")
            
    except Exception as e:
        print(f"⚠️ Помилка при обробці: {e}")

if __name__ == "__main__":
    main()
