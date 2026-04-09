import json
from datetime import datetime, timedelta
import os
import requests
import re
import random
from zoneinfo import ZoneInfo
from google import genai

# --- КОНФІГУРАЦІЯ ТА ШІ ---
kyiv_tz = ZoneInfo("Europe/Kiev")
LAT, LON = 50.2699, 34.3961
MODEL_NAME = 'gemini-2.0-flash'
STATE_PATH = 'scripts/state.json'

def get_ai_client():
    api_key = os.getenv('GEMINI_API_KEY')
    return genai.Client(api_key=api_key) if api_key else None

# --- ФОРМАТУВАННЯ ---
def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    text = str(text).replace('\\', '\\\\')
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

# --- ПОГОДА (НОВИЙ ДИНАМІЧНИЙ БЛОК) ---
def get_weather_desc(code):
    codes = {
        0: "Ясно, сонячно", 1: "Малохмарно", 2: "Мінлива хмарність", 3: "Хмарно",
        45: "Туман", 48: "Паморозь", 51: "Легкий дощ", 61: "Дощ", 63: "Сильний дощ",
        71: "Легкий сніг", 73: "Сніг", 75: "Сильний сніг", 80: "Злива", 95: "Гроза"
    }
    return codes.get(code, "Мінлива хмарність")

def get_weather_data():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=temperature_2m,weathercode&timezone=Europe/Kiev&forecast_days=3"
    try:
        r = requests.get(url, headers={'User-Agent': 'MykolayivkaBot'}, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def check_and_send_weather(now, state):
    hour = now.hour
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    w_raw = get_weather_data()
    if not w_raw or 'hourly' not in w_raw: return False

    if 18 <= hour:
        seg, target_date, ctx = "night_full", tomorrow_str, "на завтра"
        h_idx = 24
        info = (f"Ранок (08:00): {get_weather_desc(w_raw['hourly']['weathercode'][h_idx+8])}, {w_raw['hourly']['temperature_2m'][h_idx+8]}°C. "
                f"День (14:00): {get_weather_desc(w_raw['hourly']['weathercode'][h_idx+14])}, {w_raw['hourly']['temperature_2m'][h_idx+14]}°C. "
                f"Вечір (20:00): {get_weather_desc(w_raw['hourly']['weathercode'][h_idx+20])}, {w_raw['hourly']['temperature_2m'][h_idx+20]}°C.")
    elif 5 <= hour < 12:
        seg, target_date, ctx = "morning_update", today_str, "на сьогодні"
        info = (f"Зараз: {get_weather_desc(w_raw['hourly']['weathercode'][hour])}, {w_raw['hourly']['temperature_2m'][hour]}°C. "
                f"Вдень очікується: {get_weather_desc(w_raw['hourly']['weathercode'][14])}, {w_raw['hourly']['temperature_2m'][14]}°C.")
    elif 12 <= hour < 18:
        seg, target_date, ctx = "evening_update", today_str, "на вечір"
        info = (f"Зараз: {get_weather_desc(w_raw['hourly']['weathercode'][hour])}, {w_raw['hourly']['temperature_2m'][hour]}°C. "
                f"Увечері (20:00): {get_weather_desc(w_raw['hourly']['weathercode'][20])}, {w_raw['hourly']['temperature_2m'][20]}°C.")
    else: return False

    state_key = f"w_{target_date}_{seg}"
    if state.get("last_weather_key") == state_key: return False

    client = get_ai_client()
    if not client: return False

    prompt = (f"Ти — бот селища Миколаївка. Напиши детальний прогноз погоди {ctx}.\n"
              f"Дані по годинах: {info}\n"
              "Обов'язково наголоси на змінах погоди протягом дня. Пиши живо з емодзі. MarkdownV2.")
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        if response.text:
            msg = f"{response.text.strip()}\n\n📊 *Сайт:* https://mixaua\\.github\\.io/Mykolayivka/"
            send_telegram_message(msg) # Текст ескейпиться всередині або самим Gemini
            state["last_weather_key"] = state_key
            return True
    except: pass
    return False

# --- ПOРАДИ ТА ЛІТЕРАТУРА (ТВІЙ ОРИГІНАЛ) ---
def get_legacy_tip(event_type):
    tips_off = [
        "🌗 Зараз стане трішки темніше, але це не надовго. Заряджайте пристрої!",
        "⏸️ Світло вимкнуть ненадовго. Час для теплого настрою та філіжанки кави.",
        "🔋 Перевірте павербанки! Скоро переходимо на автономний режим.",
        "🌘 Темрява — це просто відсутність світла, а не надії. Тримайтеся!",
        "⚡ Готуємось до відключення. Все буде Україна!",
        "🕯️ Час підготувати свічки та ліхтарики. Ми впораємося, ми разом!",
        "📱 Останній шанс зарядити гаджети. Блекаут вже поруч!",
        "💪 Ще одне відключення — ще один шанс почути тишу і зібратись з думками. Тримаємось!",
        "🌃 Пора перевірити автономні джерела живлення. Скоро темрява.",
        "🔦 Приготуйте ліхтарики та павербанки. Світло ненадовго піде на перепочинок.",
        "☕ Час для затишку при свічках. Все буде добре!"
    ]
    tips_on = [
        "⏳ От-от з'явиться світло! Готуйтеся вмикати улюблені прилади.",
        "🔋 Скоро буде світло. Життя повертається у звичний ритм!",
        "💡 Світло вже на підході. Блекаут тимчасово відступив!",
        "🔥 Світло повертається! Дякуємо енергетикам за працю.",
        "✨ Ще кілька хвилин — і будемо з електрикою. Гарного вам настрою!",
        "🎉 Готуйте чайники! Світло вже майже тут. А це значить час запашної кави",
        "⚡ На зв'язку гарні новини! Незабаром запалаємо лампочки і настрій.",
        "🌟 Світло повертається. Тримайтеся, ще трохи!",
        "💫 Електрика вже в дорозі. Підготуйте список справ!",
        "🔌 Розетки знову в грі! Скоро можна буде все підключити.",
        "☀️ Цей час невпинно наближається! Світло майже тут."
    ]
    return random.choice(tips_off if event_type == "off" else tips_on)

def get_literature_tip(event_type, state):
    lit_path = 'scripts/literature.json'
    try:
        with open(lit_path, 'r', encoding='utf-8') as f: lit_data = json.load(f)
    except: return None

    key = "ON_event" if event_type == "on" else "OFF_event"
    quotes = lit_data.get(key, [])
    if not quotes: return None

    idx_key = f"{key}_index"
    current_idx = state.get(idx_key, 0)
    quote = quotes[current_idx % len(quotes)]
    state[idx_key] = (current_idx + 1) % len(quotes)
    return quote

# --- ВІДПРАВКА (ТВІЙ ОРИГІНАЛ) ---
def send_telegram_message(message_text):
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message_text, 'parse_mode': 'MarkdownV2'}
    requests.post(url, json=payload)

def send_literature_notif(quote, event_type):
    on_greetings = ["Оце прокинувся раніше...", "Тихо зазирнув у ваші плани...", "Привіт! До увімкнення ще є час...", "Я тут на мить прокинувся...", "Мої датчики кажуть, що скоро буде світло!", "Вітаю друзі! Провів невеликий моніторинг...", "Привітання від вашого помічника!", "Пробудився трохи раніше...", "Привіт! Пробіг повз серверну...", "Ваш бот на зв'язку!", "Заглянув перевірити ситуацію..."]
    off_greetings = ["Зайшов перевірити, як ви тут...", "Друзі, зазирнув у графік...", "Пробігав повз і вирішив нагадати...", "Перевірив черги... Так, скоро вимкнення.", "Бот на зв'язку! Бачу, що скоро...", "Привіт! Перевірив розклад...", "Привіт! Заглянув у систему...", "Ваш електронний товариш знову тут!", "Вітаю друзі! Моніторив графік...", "Зайшов перевірити стан справ...", "Вітаю! Переглянув розклад..."]
    title = "💡 *Передчуття світла\\.\\.\\.*" if event_type == "on" else "🌙 *Роздуми при свічках\\.\\.\\.*"
    greeting = random.choice(on_greetings if event_type == "on" else off_greetings)
    msg = (f"{title}\n\n🤖 _{escape_markdown_v2(greeting)}_\n\n📖 *«{escape_markdown_v2(quote.get('text', ''))}»*\n\n"
           f"👤 *{escape_markdown_v2(quote.get('author', ''))}*\n{escape_markdown_v2(quote.get('about_author', ''))}\n\n"
           f"📚 *Про текст:* {escape_markdown_v2(quote.get('about_text', ''))}\n\n✍️ _Підготував: {escape_markdown_v2(quote.get('prepared_by', ''))}_")
    send_telegram_message(msg)

def send_notif(cur_time, day, start, end, diff, type, future_events):
    icon = get_time_icon(start)
    status = "увімкнуть світло\\! 💡" if type == "on" else "вимкнуть світло\\! ⚡"
    event_label = "Увімкнення" if type == "on" else "Вимкнення"
    time_info = "За графіком до кінця доби" if (type == "on" and end is None) else f"{escape_markdown_v2(format_time_display(start))} \\- {escape_markdown_v2(format_time_display(end))} \\({escape_markdown_v2(calculate_duration_from_min(start, end))}\\)"
    next_list = [f"👉 Вимкнення: {escape_markdown_v2(format_time_display(fev['start']))} \\- {escape_markdown_v2(format_time_display(fev['end']))}" for fev in future_events if fev['start'] < 2880]
    next_events_block = ("\n\n*Наступні:*\n" + "\n".join(next_list)) if next_list else ""
    msg = (f"{icon} *Увага\\! Менше ніж за {escape_markdown_v2(str(int(diff)))} хвилин {status}*\n\n"
           f"📅 {escape_markdown_v2(day)}, {escape_markdown_v2(cur_time)}\n⏰ {event_label}: {time_info}{next_events_block}\n\n"
           f"💡 _{escape_markdown_v2(get_legacy_tip(type))}_\n\n📊 *Графік:* https://mixaua\\.github\\.io/Mykolayivka/")
    send_telegram_message(msg)

# --- ЛОГІКА ЗАПУСКУ ---
def run_bot():
    try:
        with open('database.json', 'r', encoding='utf-8') as f: data = json.load(f)
    except: return
    now = datetime.now(kyiv_tz)
    now_m = now.hour * 60 + now.minute
    state = {"ON_event_index": 0, "OFF_event_index": 0}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, 'r', encoding='utf-8') as f: state = json.load(f)
        except: pass

    # ПЕРЕВІРКА ПОГОДИ
    check_and_send_weather(now, state)

    # ЛОГІКА ГРАФІКА
    days_ukr_cap = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "П'ятниця", 5: "Субота", 6: "Неділя"}
    days_ukr = {k: v.lower() for k, v in days_ukr_cap.items()}
    today_dow = now.weekday()
    all_events = []
    for day_offset in range(2):
        target_dow = (today_dow + day_offset) % 7
        schedule = data.get('queues', {}).get('6.2', {}).get(days_ukr[target_dow], [])
        for val in schedule:
            s_str, e_str = val.split('-')
            sh, sm = map(int, s_str.split(':')); eh, em = map(int, e_str.split(':'))
            st = sh * 60 + sm + (day_offset * 1440)
            et = (1440 if (eh == 0 and em == 0) or eh == 24 else eh * 60 + em) + (day_offset * 1440)
            all_events.append({'start': st, 'end': et})
    
    all_events.sort(key=lambda x: x['start'])
    merged = []
    if all_events:
        curr = all_events[0]
        for nxt in all_events[1:]:
            if curr['end'] == nxt['start']: curr['end'] = nxt['end']
            else: merged.append(curr); curr = nxt
        merged.append(curr)

    for i, ev in enumerate(merged):
        if ev['start'] <= now_m < ev['end']:
            diff = ev['end'] - now_m
            if 0 < diff <= 30:
                send_notif(now.strftime("%H:%M"), days_ukr_cap[today_dow], ev['end'], (merged[i+1]['start'] if i+1 < len(merged) else None), diff, "on", merged[i+1:])
                break
            elif 70 < diff <= 90:
                q = get_literature_tip("on", state)
                if q: send_literature_notif(q, "on")
                break
        elif ev['start'] > now_m:
            diff = ev['start'] - now_m
            if 0 < diff <= 30:
                send_notif(now.strftime("%H:%M"), days_ukr_cap[today_dow], ev['start'], ev['end'], diff, "off", merged[i+1:])
                break
            elif 70 < diff <= 90:
                q = get_literature_tip("off", state)
                if q: send_literature_notif(q, "off")
                break

    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_bot()
