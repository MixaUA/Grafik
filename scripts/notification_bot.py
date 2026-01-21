import json
from datetime import datetime
import os
import requests
import re
import random
import textwrap

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    text = text.replace('\\', '\\\\')
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def smart_wrap(text, width=60):
    lines = textwrap.wrap(text, width=width, break_long_words=False)
    return "\n".join(lines)

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

def get_random_tip(event_type):
    tips_off = [
        "🌗 Зараз стане трішки темніше навколо, але не всередині.",
        "⏸️ Світло вимкнуть ненадовго. Завершуй справи з електрикою - решта почекає.",
        "💾 Світло от-от зникне. Якщо працюєш за ПК - збережи важливе й дай йому відпочити.",
        "🕯️ Світло зникне на якийсь час. Подбай про важливе - решта почекає.",
        "🌘 Світло повільно зникає. Подбай про те, що має значення саме зараз.",
        "🔌 Невелика перерва в електриці. Можеш спокійно завершити справи й підготуватись."
    ]
    tips_on = [
        "⏳ От-от з’явиться світло. На жаль на короткий проміжок часу, не витрачай його даремно!",
        "🔋 Скоро буде світло. Подумай, що варто зарядити в першу чергу.",
        "🔌 Світло скоро ввімкнуть. Підготуй важливе - без поспіху.",
        "🚀 Світло на підході! Готуйся вмикати найважливіші прилади.",
        "📱 Скоро з’явиться напруга. Перевір, чи готові твої гаджети до зарядки.",
        "🌟 Світло ось-ось повернеться. Використай цей час максимально ефективно!"
    ]
    raw_tip = random.choice(tips_off if event_type == "off" else tips_on)
    return smart_wrap(raw_tip, width=60)

def send_telegram_message(message_text):
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message_text, 'parse_mode': 'MarkdownV2'}
    try:
        requests.post(url, json=payload).raise_for_status()
    except Exception as e:
        print(f"Error: {e}")

def run_bot():
    try:
        with open('database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except: return

    now = datetime.now()
    now_m = now.hour * 60 + now.minute
    current_time_str = now.strftime("%H:%M")
    days_ukr_cap = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "П'ятниця", 5: "Субота", 6: "Неділя"}
    days_ukr = {k: v.lower() for k, v in days_ukr_cap.items()}
    today_dow = now.weekday()

    all_events = []
    for day_offset in range(2):
        target_dow = (today_dow + day_offset) % 7
        schedule = data.get('queues', {}).get('6.2', {}).get(days_ukr[target_dow], [])
        for val in schedule:
            s_str, e_str = val.split('-')
            sh, sm = map(int, s_str.split(':'))
            eh, em = map(int, e_str.split(':'))
            st = sh * 60 + sm + (day_offset * 1440)
            et = (1440 if (eh == 0 and em == 0) or eh == 24 else eh * 60 + em) + (day_offset * 1440)
            all_events.append({'start': st, 'end': et})

    if not all_events: return
    all_events.sort(key=lambda x: x['start'])
    
    merged = []
    curr = all_events[0]
    for nxt in all_events[1:]:
        if curr['end'] == nxt['start']:
            curr['end'] = nxt['end']
        else:
            merged.append(curr)
            curr = nxt
    merged.append(curr)
    
    for i, ev in enumerate(merged):
        # ЛОГІКА ДЛЯ УВІМКНЕННЯ (ми зараз у темряві)
        if ev['start'] <= now_m < ev['end']:
            diff = ev['end'] - now_m
            if 0 < diff <= 30:
                # Визначаємо період СВІТЛА, що настане
                light_start = ev['end']
                light_end = merged[i+1]['start'] if i+1 < len(merged) else (ev['end'] + 120) # +2 год як заглушка якщо далі нема даних
                send_notif(current_time_str, days_ukr_cap[today_dow], light_start, light_end, diff, "on", merged[i+1:])
                break
        # ЛОГІКА ДЛЯ ВИМКНЕННЯ (зараз світло є)
        elif ev['start'] > now_m:
            diff = ev['start'] - now_m
            if 0 < diff <= 30:
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['start'], ev['end'], diff, "off", merged[i+1:])
                break

def send_notif(cur_time, day, start, end, diff, type, future_events):
    s_t = escape_markdown_v2(format_time_display(start))
    e_t = escape_markdown_v2(format_time_display(end))
    dur = escape_markdown_v2(calculate_duration_from_min(start, end))
    
    if type == "off":
        icon = get_time_icon(start)
        status = "вимкнуть світло\\! ⚡"
        event_label = "Вимкнення"
    else:
        icon = get_time_icon(start) # іконка початку періоду світла
        status = "увімкнуть світло\\! 💡"
        event_label = "Увімкнення"
    
    next_list = []
    for fev in future_events:
        if fev['start'] < 1440:
            f_s = escape_markdown_v2(format_time_display(fev['start']))
            f_e = escape_markdown_v2(format_time_display(fev['end']))
            f_d = escape_markdown_v2(calculate_duration_from_min(fev['start'], fev['end']))
            next_list.append(f"👉 Вимкнення: {f_s} \\- {f_e} \\({f_d}\\)")
    
    next_events_block = ""
    if next_list:
        next_events_block = "\n\n*Наступні:*\n" + "\n".join(next_list)

    msg = (
        f"{icon} *Увага\\! Менше ніж за {escape_markdown_v2(str(int(diff)))} хвилин {status}*\n\n"
        f"📅 {escape_markdown_v2(day)}, {escape_markdown_v2(cur_time)}\n"
        f"⏰ {event_label}: {s_t} \\- {e_t} \\({dur}\\)"
        f"{next_events_block}\n\n"
        f"{escape_markdown_v2(get_random_tip(type))}\n\n"
        f"📊 *Графік:* https://mixaua\\.github\\.io/Mykolayivka/"
    )
    send_telegram_message(msg)

if __name__ == "__main__":
    run_bot()
