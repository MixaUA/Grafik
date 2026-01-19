import json
from datetime import datetime, timedelta
import os
import requests
import re
import random

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    text = text.replace('\\', '\\\\')
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
    if 6 <= hour < 12: return "🌅"
    elif 12 <= hour < 18: return "☀️"
    elif 18 <= hour < 22: return "🌆"
    else: return "🌙"

def get_random_tip(event_type):
    # Оновлені поради згідно з нашими домовленостями:
    tips_off = [
        "🌗 Зараз стане трішки темніше навколо, але не всередині\\.",
        "⏸️ Світло вимкнуть ненадовго\\. Завершуй справи з електрикою \\— решта почекає\\.",
        "💾 Світло от\\-от зникне\\. Якщо працюєш за ПК \\— збережи важливе й дай йому відпочити\\.",
        "🕯️ Світло зникне на якийсь час\\. Подбай про важливе \\— решта почекає\\.",
        "🌘 Світло повільно зникає\\. Подбай про те, що має значення саме зараз\\.",
        "🔌 Невелика перерва в електриці\\. Можеш спокійно завершити справи й підготуватись\\."
    ]
    tips_on = [
        "⏳ От\\-от з’явиться світло\\. На жаль на короткий проміжок часу, не витрачай його даремно\\!",
        "🔋 Скоро буде світло\\. Подумай, що варто зарядити в першу чергу\\.",
        "🔌 Світло скоро ввімкнуть\\. Підготуй важливе \\— без поспіху\\.",
        "🚀 Світло на підході\\! Готуйся вмикати найважливіші прилади\\.",
        "📱 Скоро з’явиться напруга\\. Перевір, чи готові твої гаджети до зарядки\\.",
        "🌟 Світло ось\\-ось повернеться\\. Використай цей час максимально ефективно\\!"
    ]
    return random.choice(tips_off if event_type == "off" else tips_on)

def send_telegram_message(message_text):
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("Помилка: Токен або ID чату не знайдені.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message_text, 'parse_mode': 'MarkdownV2'}
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
    
    print(f"Зараз: {current_time_str}, {days_ukr[today_dow]}")

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
        print("Вихід: Графік порожній.")
        return

    all_events.sort(key=lambda x: x['start'])
    merged = []
    curr = all_events[0]
    for next_ev in all_events[1:]:
        if curr['end'] == next_ev['start']:
            curr['end'] = next_ev['end']
        else:
            merged.append(curr)
            curr = next_ev
    merged.append(curr)
    
    print(f"Виявлено {len(merged)} склеєних інтервалів відключень:")
    for i, ev in enumerate(merged, 1):
        print(f"   {i}. {format_time_display(ev['start'])} — {format_time_display(ev['end'])}")

    past_count, past_hours, future_count, future_hours = 0, 0, 0, 0
    for ev in merged:
        if ev['start'] < 1440:
            actual_end = min(ev['end'], 1440)
            duration = (actual_end - ev['start']) / 60
            if actual_end <= now_m:
                past_count += 1
                past_hours += int(duration)
            else:
                future_count += 1
                future_hours += int(duration)

    notified = False
    for i, ev in enumerate(merged):
        start_s, end_s = format_time_display(ev['start']), format_time_display(ev['end'])
        
        if ev['start'] <= now_m < ev['end']:
            diff = ev['end'] - now_m
            print(f"Перевірка [{start_s}-{end_s}]: Ми в блоці. До ВВІМКНЕННЯ: {int(diff)} хв.")
            if 0 < diff <= 30:
                print(f"==> УМОВА 30 ХВ: Надсилаю про світло")
                if i + 1 < len(merged):
                    next_off_start = merged[i + 1]['start']
                else:
                    next_off_start = 1440
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['end'], next_off_start, diff, past_count, past_hours, future_count, future_hours, "on")
                notified = True
                break
        elif ev['start'] > now_m:
            diff = ev['start'] - now_m
            print(f"Перевірка [{start_s}-{end_s}]: Світло є. До ВИМКНЕННЯ: {int(diff)} хв.")
            if 0 < diff <= 30:
                print(f"==> УМОВА 30 ХВ: Надсилаю про вимкнення")
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['start'], ev['end'], diff, past_count, past_hours, future_count, future_hours, "off")
                notified = True
                break

    if not notified:
        print("Підсумок: Подій у вікні 30 хв не знайдено. Бот завершив роботу.")

def send_notif(cur_time, day, start, end, diff, p_c, p_h, f_c, f_h, type):
    start_time = escape_markdown_v2(format_time_display(start))
    end_time = escape_markdown_v2(format_time_display(end))
    duration = escape_markdown_v2(calculate_duration_from_min(start, end))
    
    if type == "off":
        icon = get_time_icon(start)
        status = "вимкнуть світло\\! ⚡"
        event_label = "Вимкнення"
    else:
        icon = get_time_icon(end)
        status = "увімкнуть світло\\! 💡"
        event_label = "Увімкнення"
    
    msg = (
        f"{icon} *Увага\\! Менше ніж за {escape_markdown_v2(str(int(diff)))} хвилин {status}*\n\n"
        f"📅 {escape_markdown_v2(day)}, {escape_markdown_v2(cur_time)}\n"
        f"⏰ {event_label}: {start_time} \\- {end_time} \\({duration}\\)\n\n"
        f"{get_random_tip(type)}\n\n"
        f"📊 Графік: https://mixaua\\.github\\.io/Grafik/"
    )
    send_telegram_message(msg)

if __name__ == "__main__":
    run_bot()
