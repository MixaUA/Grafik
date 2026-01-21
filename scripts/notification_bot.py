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
        "🔌 Світло скоро ввімкнуть. Подбай про важливе - без поспіху.",
        "🚀 Світло на підході! Готуйся вмикати найважливіші прилади.",
        "📱 Скоро з’явиться напруга. Перевір, чи готові твої гаджети до зарядки.",
        "🌟 Світло ось-ось повернеться. Використай цей час максимально ефективно!"
    ]
    raw_tip = random.choice(tips_off if event_type == "off" else tips_on)
    return smart_wrap(raw_tip, width=60)

def send_telegram_message(message_text):
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("❌ Помилка: Токени Telegram не знайдені!")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message_text, 'parse_mode': 'MarkdownV2'}
    try:
        requests.post(url, json=payload).raise_for_status()
        print("✅ Повідомлення успішно надіслано в Telegram.")
    except Exception as e:
        print(f"❌ Помилка відправки в Telegram: {e}")

def run_bot():
    try:
        with open('database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Не вдалося відкрити database.json: {e}")
        return

    now = datetime.now()
    now_m = now.hour * 60 + now.minute
    current_time_str = now.strftime("%H:%M")
    days_ukr_cap = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "П'ятниця", 5: "Субота", 6: "Неділя"}
    days_ukr = {k: v.lower() for k, v in days_ukr_cap.items()}
    today_dow = now.weekday()

    print(f"🕒 Поточний час: {current_time_str}, {days_ukr_cap[today_dow]}")

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

    if not all_events:
        print("ℹ️ Подій у графіку не знайдено.")
        return

    all_events.sort(key=lambda x: x['start'])
    
    merged = []
    curr = all_events[0]
    for nxt in all_events[1:]:
        if curr['end'] == nxt['start']: curr['end'] = nxt['end']
        else:
            merged.append(curr)
            curr = nxt
    merged.append(curr)
    
    print("📅 Знайдені періоди вимкнення (склеєні):")
    for m in merged:
        print(f"   - {format_time_display(m['start'])} до {format_time_display(m['end'])}")

    sent = False
    for i, ev in enumerate(merged):
        if ev['start'] <= now_m < ev['end']:
            diff = ev['end'] - now_m
            if 0 < diff <= 30:
                print(f"🔔 Спрацював тригер на УВІМКНЕННЯ (залишилось {int(diff)} хв)")
                light_start = ev['end']
                next_ev = merged[i+1] if i+1 < len(merged) else None
                if next_ev and next_ev['start'] < 1440:
                    send_notif(current_time_str, days_ukr_cap[today_dow], light_start, next_ev['start'], diff, "on", merged[i+1:])
                else:
                    send_notif(current_time_str, days_ukr_cap[today_dow], light_start, None, diff, "on", merged[i+1:])
                sent = True
                break
        elif ev['start'] > now_m:
            diff = ev['start'] - now_m
            if 0 < diff <= 30:
                print(f"🔔 Спрацював тригер на ВИМКНЕННЯ (залишилось {int(diff)} хв)")
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['start'], ev['end'], diff, "off", merged[i+1:])
                sent = True
                break
    
    if not sent:
        print("😴 Умов для відправки повідомлення зараз немає.")

def send_notif(cur_time, day, start, end, diff, type, future_events):
    if type == "off":
        icon = get_time_icon(start)
        status = "вимкнуть світло\\! ⚡"
        event_label = "Вимкнення"
        time_info = f"{escape_markdown_v2(format_time_display(start))} \\- {escape_markdown_v2(format_time_display(end))} \\({escape_markdown_v2(calculate_duration_from_min(start, end))}\\)"
    else:
        icon = get_time_icon(start)
        status = "увімкнуть світло\\! 💡"
        event_label = "Увімкнення"
        if end is None:
            time_info = "За графіком до кінця доби"
        else:
            time_info = f"{escape_markdown_v2(format_time_display(start))} \\- {escape_markdown_v2(format_time_display(end))} \\({escape_markdown_v2(calculate_duration_from_min(start, end))}\\)"
    
    next_list = []
    for fev in future_events:
        if fev['start'] < 2880:
            f_s = escape_markdown_v2(format_time_display(fev['start']))
            f_e = escape_markdown_v2(format_time_display(fev['end']))
            f_d = escape_markdown_v2(calculate_duration_from_min(fev['start'], fev['end']))
            next_list.append(f"👉 Вимкнення: {f_s} \\- {f_e} \\({f_d}\\)")
    
    next_events_block = ("\n\n*Наступні:*\n" + "\n".join(next_list)) if next_list else ""

    msg = (
        f"{icon} *Увага\\! Менше ніж за {escape_markdown_v2(str(int(diff)))} хвилин {status}*\n\n"
        f"📅 {escape_markdown_v2(day)}, {escape_markdown_v2(cur_time)}\n"
        f"⏰ {event_label}: {time_info}"
        f"{next_events_block}\n\n"
        f"{escape_markdown_v2(get_random_tip(type))}\n\n"
        f"📊 *Графік:* https://mixaua\\.github\\.io/Mykolayivka/"
    )
    send_telegram_message(msg)

if __name__ == "__main__":
    run_bot()
