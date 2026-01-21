import json
from datetime import datetime, timedelta
import os
import requests
import re
import random
import textwrap

# --- НАЛАШТУВАННЯ ФАЙЛІВ ---
LIT_FILE = 'literature.json'
STATE_FILE = 'state.json'

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    text = str(text).replace('\\', '\\\\') # Ensure text is string and escape backslashes first
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_time_display(total_minutes):
    h = (int(total_minutes) // 60) % 24
    m = int(total_minutes) % 60
    return f"{h:02d}:{m:02d}"

def calculate_duration_from_min(start_m, end_m):
    total_minutes = int(end_m - start_m)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0 and minutes > 0: return f"{hours} год. {minutes} хв."
    elif hours > 0: return f"{hours} год."
    elif minutes > 0: return f"{minutes} хв."
    return "0 хв."

def get_time_icon(total_minutes):
    hour = (int(total_minutes) // 60) % 24
    return "☀️" if 6 <= hour < 20 else "🌙"

def smart_wrap(text, width=60):
    lines = textwrap.wrap(text, width=width, break_long_words=False)
    return "\n".join(lines)

def get_next_quote(event_type):
    """Отримує наступну цитату з literature.json по черзі, використовуючи state.json"""
    if not os.path.exists(LIT_FILE):
        print(f"DEBUG: Literature file {LIT_FILE} not found.")
        return None
    
    try:
        with open(LIT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Помилка читання бази літератури: {e}")
        return None

    key = "ON_event" if event_type == "on" else "OFF_event"
    idx_key = "ON_index" if event_type == "on" else "OFF_index"
    quotes = data.get(key, [])

    if not quotes:
        print(f"DEBUG: No quotes found for {event_type} in {LIT_FILE}.")
        return None

    # Читаємо або створюємо стан черговості
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except: # Handle malformed state.json or other read errors
            state = {"ON_index": 0, "OFF_index": 0}
            print(f"DEBUG: Re-initializing state.json due to error.")
    else:
        state = {"ON_index": 0, "OFF_index": 0}
        print(f"DEBUG: Initializing new state.json.")

    # Визначаємо індекс
    current_idx = state.get(idx_key, 0)
    if current_idx >= len(quotes):
        current_idx = 0
    
    selected_quote = quotes[current_idx]

    # Оновлюємо індекс для наступного разу
    state[idx_key] = (current_idx + 1) % len(quotes)
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Помилка збереження state.json: {e}")
    
    print(f"DEBUG: Retrieved quote ID {selected_quote.get('id', 'N/A')} for {event_type} event. Next index: {state[idx_key]}")
    return selected_quote

def send_telegram_message(message_text):
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("Помилка: Токен або ID чату не знайдені.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'MarkdownV2',
        'disable_web_page_preview': True  # Disable link previews
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Повідомлення успішно надіслано в Telegram.")
    except Exception as e:
        print(f"Помилка відправки в ТГ: {e}")

def run_bot():
    print(f"--- Запуск бота: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    try:
        with open('database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Файл database.json завантажено.")
    except Exception as e:
        print(f"Помилка завантаження файлу: {e}")
        return

    now = datetime.now()
    now_m = now.hour * 60 + now.minute
    current_time_str = now.strftime("%H:%M")
    days_ukr = {0: "понеділок", 1: "вівторок", 2: "середа", 3: "четвер", 4: "п'ятниця", 5: "субота", 6: "неділя"}
    days_ukr_cap = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "П'ятниця", 5: "Субота", 6: "Неділя"}
    today_dow = now.weekday()
    
    print(f"DEBUG: Зараз: {current_time_str}, {days_ukr_cap[today_dow]}")

    all_events = []
    for day_offset in range(2):
        target_dow = (today_dow + day_offset) % 7
        schedule = data.get('queues', {}).get('6.2', {}).get(days_ukr[target_dow], [])
        for val in schedule:
            s_str, e_str = val.split('-')
            s_h, s_m = map(int, s_str.split(':'))
            e_h, e_m = map(int, e_str.split(':'))
            start_total = s_h * 60 + s_m + (day_offset * 1440)
            end_total = (1440 if (e_h == 0 and e_m == 0) or e_h == 24 else e_h * 60 + e_m) + (day_offset * 1440)
            all_events.append({'start': start_total, 'end': end_total})

    if not all_events:
        print("DEBUG: Вихід: Графік порожній.")
        return

    all_events.sort(key=lambda x: x['start'])
    merged = []
    if all_events:
        curr = all_events[0]
        for next_ev in all_events[1:]:
            if curr['end'] == next_ev['start']:
                curr['end'] = next_ev['end']
            else:
                merged.append(curr)
                curr = next_ev
        merged.append(curr)
    
    print(f"DEBUG: Виявлено {len(merged)} склеєних інтервалів відключень:")
    for i, ev in enumerate(merged, 1):
        print(f"DEBUG:    {i}. {format_time_display(ev['start'])} — {format_time_display(ev['end'])}")

    notified = False
    for i, ev in enumerate(merged):
        start_s, end_s = format_time_display(ev['start']), format_time_display(ev['end'])
        
        if ev['start'] <= now_m < ev['end']:
            diff = ev['end'] - now_m
            print(f"DEBUG: Перевірка [{start_s}-{end_s}]. Ми в блоці. До ВВІМКНЕННЯ: {int(diff)} хв.")
            if 0 < diff <= 30:
                print(f"DEBUG: ==> УМОВА 30 ХВ: Надсилаю про світло")
                next_off_start = merged[i + 1]['start'] if i + 1 < len(merged) else 1440
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['end'], ev['start'], diff, "on", merged[i+1:])
                notified = True
                break
        elif ev['start'] > now_m:
            diff = ev['start'] - now_m
            print(f"DEBUG: Перевірка [{start_s}-{end_s}]. Світло є. До ВИМКНЕННЯ: {int(diff)} хв.")
            if 0 < diff <= 30:
                print(f"DEBUG: ==> УМОВА 30 ХВ: Надсилаю про вимкнення")
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['start'], ev['end'], diff, "off", merged[i+1:])
                notified = True
                break

    if not notified:
        print("DEBUG: Підсумок: Подій у вікні 30 хв не знайдено. Бот завершив роботу.")

def send_notif(cur_time, day, start_event_m, end_event_m, diff, type, future_events=[]):
    # Системна інформація для логування та повідомлення
    day_esc = escape_markdown_v2(day)
    time_esc = escape_markdown_v2(cur_time)
    diff_esc = escape_markdown_v2(str(int(diff)))
    
    if type == "off":
        icon = get_time_icon(start_event_m)
        status = "вимкнуть світло\\! ⚡"
        event_label = "Вимкнення"
    else:
        icon = get_time_icon(end_event_m)
        status = "увімкнуть світло\\! 💡"
        event_label = "Увімкнення"

    # Отримуємо цитату з літературного джейсона
    q = get_next_quote(type)
    
    if q:
        # Поля вже екрановані в JSON, використовуємо їх напряму
        author = q.get('author', 'Невідомий автор')
        text = q.get('text', 'Текст цитати відсутній.')
        a_author = q.get('about_author', 'Інформація про автора відсутня.')
        a_text = q.get('about_text', 'Інформація про текст відсутня.')
        prep = q.get('prepared_by', 'Admin')

        raw_quote_block = (
            f"📖 *Хвилинка класики:*
"
            f"👤 *{author}*

"
            f"«{text}»

"
            f"ℹ️ *Про автора:* {a_author}
"
            f"📝 *Про текст:* {a_text}

"
            f"✍️ *Підготував:* {prep}"
        )
        quote_block = smart_wrap(raw_quote_block)
    else:
        quote_block = smart_wrap("Тримаймося\\! Світло переможе темряву\.")
        print(f"DEBUG: No quote retrieved for {type}. Using fallback message.")

    next_list = []
    # Limit to next 3 events to avoid long messages
    for fev in future_events[:3]:
        if fev['start'] < 1440: 
            f_s = escape_markdown_v2(format_time_display(fev['start']))
            f_e = escape_markdown_v2(format_time_display(fev['end']))
            f_d = escape_markdown_v2(calculate_duration_from_min(fev['start'], fev['end']))
            next_list.append(f"👉 Вимкнення: {f_s} \- {f_e} \({f_d}\)")

    next_events_block = ""
    if next_list:
        next_events_block = "\n\n*Наступні:*
" + "\n".join(next_list)
    
    # Construct final message
    msg = (
        f"{icon} *Увага\\! Менше ніж за {diff_esc} хвилин {status}*

"
        f"📅 {day_esc}, {time_esc}
"
        f"⏰ {event_label}: {escape_markdown_v2(format_time_display(start_event_m))} \- {escape_markdown_v2(format_time_display(end_event_m))} \({escape_markdown_v2(calculate_duration_from_min(start_event_m, end_event_m))}\)"
        f"{next_events_block}

"
        f"{quote_block}

"
        f"📊 *Графік:* https://mixaua\\.github\\.io/Mykolayivka/"
    )
    
    print(f"DEBUG: Constructed msg (truncated): {msg[:200]}...")
    send_telegram_message(msg)

if __name__ == "__main__":
    run_bot()
