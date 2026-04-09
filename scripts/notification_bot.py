import json
from datetime import datetime, timedelta
import os
import requests
import re
import random

# --- НАЛАШТУВАННЯ ПОГОДИ ---
WEATHER_API = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=50.2699&longitude=34.3961"
    "&hourly=temperature_2m,apparent_temperature,precipitation_probability,"
    "precipitation,weathercode,windspeed_10m,winddirection_10m,cloudcover"
    "&daily=weathercode,temperature_2m_max,temperature_2m_min"
    "&timezone=Europe%2FKiev&forecast_days=3"
)

SITE_URL = "https://mixaua\\.github\\.io/Mykolayivka/"

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

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

# --- ПОРАДИ (РАНДОМ) ---
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

# --- ЛІТЕРАТУРНИЙ БЛОК ---
def get_literature_tip(event_type):
    lit_path = 'scripts/literature.json'
    state_path = 'scripts/state.json'
    try:
        with open(lit_path, 'r', encoding='utf-8') as f:
            lit_data = json.load(f)
    except Exception as e:
        print(f"❌ Помилка завантаження literature.json: {e}")
        return None

    key = "ON_event" if event_type == "on" else "OFF_event"
    quotes = lit_data.get(key, [])
    if not quotes: return None

    state = {"ON_event_index": 0, "OFF_event_index": 0}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except: pass

    idx_key = f"{key}_index"
    current_idx = state.get(idx_key, 0)
    if current_idx >= len(quotes): current_idx = 0
    
    quote = quotes[current_idx]
    print(f"📖 [LIT DEBUG] Тип: {event_type}, Взято ID: {quote.get('id')}, Автор: {quote.get('author')}")
    
    state[idx_key] = (current_idx + 1) % len(quotes)
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
    except: pass
    return quote

# --- ВІДПРАВКА ---
def send_telegram_message(message_text):
    bot_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message_text, 'parse_mode': 'MarkdownV2'}
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"⚠️ Telegram відповів помилкою: {response.status_code} — {response.text}")

def send_literature_notif(quote, event_type):
    on_greetings = [
        "Оце прокинувся подивитися, що там у нашому графіку. Бачу, що ще маю трохи часу, перш ніж бігти вмикати вам рубильники. Поки ми всі чекаємо, тримайте цікавинку, а я ще трішки подрімаю. Скоро почуємось!",
        "Тихо зазирнув у ваші плани... Світло вже на підході! Поки воно ще в дорозі, пропоную хвилинку для роздумів. Не сумуйте, скоро буде трішки світліше!",
        "Привіт! Перевірив систему — все за розкладом. До увімкнення ще є час, тож вирішив не приходити з порожніми руками. Ось вам літературна пауза від мене.",
        "Я тут на мить прокинувся... Бачу, ви теж чекаєте на вогники? Поки ми в одній команді очікування, тримайте дещо для натхнення. Повернусь, коли треба буде діяти!",
        "Мої датчики кажуть, що скоро буде світло! А поки я готуюся до старту, ось вам трохи поживи для розуму. Відпочивайте, я на зв'язку.",
        "Вітаю друзі! Провів невеликий моніторинг — світло до нас прийде незабаром. Поки ви чекаєте, ось вам дещо цікаве для душі. Я ще заскочу перед увімкненням!",
        "Привітання від вашого енергетичного помічника! Бачу, що світло вже готується до виходу. Поки воно налаштовується, тримайте літературний перекус від мене.",
        "Пробудився трохи раніше й вирішив перевірити графік. Так, світло вже майже тут! Поки ви очікуєте, ось вам щось для натхнення. До зустрічі перед ввімкненням!",
        "Привіт! Пробіг повз серверну й побачив, що світло вже на низькому старті. Поки воно готується, пропоную скоротати час за цікавою літературою.",
        "Ваш бот на зв'язку! Перевірив всі показники — увімкнення відбудеться згідно плану. А поки маємо час, тримайте невеличку цікавинку для гарного настрою!",
        "Заглянув перевірити ситуацію — все йде за планом, світло вже в дорозі! Поки ви чекаєте на електрику, ось вам дещо для роздумів. Скоро побачимось знову!"
    ]
    off_greetings = [
        "Зайшов перевірити, як ви тут. Бачу за графіком, що скоро нам доведеться трохи побути в тиші та темряві. Поки світло ще з нами, вирішив поділитися особливим словом. Зустрінемось ближче до вимкнення!",
        "Друзі, зазирнув у графік — темрява вже готує свій вихід. Поки лампи ще світять, ловіть дещо цікаве для внутрішнього тепла. Нехай ці слова зігрівають вас у темні години очікувань.",
        "Пробігав повз і вирішив нагадати: скоро відключення електрики. Поки є можливість почитати з екрана без ліхтарика — тримайте літературну цікавинку від вашого бота!",
        "Перевірив черги... Так, скоро вимкнення. Але не варто засмучуватися! Поки маємо час, пропоную трохи зануритися в літературу. А я піду перевірю свої акумулятори.",
        "Бот на зв'язку! Бачу, що скоро за планом вимкнення але не зараз. Вирішив заздалегідь підняти вам настрій добрим словом. Тримайте, а я ще повернусь із точним часом!",
        "Привіт! Перевірив розклад і бачу, що скоро відключення. Поки світло ще освітлює ваші екрани, тримайте щось для душі. Готуйте свічки, скоро повернусь!",
        "Привіт! Заглянув у систему — вимкнення вже планується. Але не поспішаймо засмучуватися! Ось вам дещо цікаве на час очікування.",
        "Ваш електронний товариш знову тут! Бачу, що блекаут уже не за горами. Поки маємо світло, давайте проведемо час з користю — тримайте літературну хвилинку!",
        "Вітаю друзі! Моніторив графік і помітив наближення відключення. Вирішив не чекати останньої хвилини та поділитися з вами чимось особливим. Тримайтеся!",
        "Зайшов перевірити стан справ — так, вимкнення на підході. Але це не привід сумувати! Ось вам дещо для натхнення перед темрявою. Повернусь ближче до події!",
        "Вітаю! Переглянув розклад і бачу, що скоро світло піде відпочивати. Поки воно ще з нами, тримайте літературну паузу від мене. До зустрічі перед відключенням!"
    ]
    title = "💡 *Передчуття світла\\.\\.\\.*" if event_type == "on" else "🌙 *Роздуми при свічках\\.\\.\\.*"
    greeting = random.choice(on_greetings if event_type == "on" else off_greetings)
    msg = (
        f"{title}\n\n"
        f"🤖 _{escape_markdown_v2(greeting)}_\n\n"
        f"📖 *«{escape_markdown_v2(quote.get('text', ''))}»*\n\n"
        f"👤 *{escape_markdown_v2(quote.get('author', ''))}*\n"
        f"{escape_markdown_v2(quote.get('about_author', ''))}\n\n"
        f"📚 *Про текст:* {escape_markdown_v2(quote.get('about_text', ''))}\n\n"
        f"✍️ _Підготував: {escape_markdown_v2(quote.get('prepared_by', ''))}_"
    )
    send_telegram_message(msg)
    print("✅ Літературне повідомлення надіслано.")

def send_notif(cur_time, day, start, end, diff, type, future_events):
    icon = get_time_icon(start)
    status = "увімкнуть світло\\! 💡" if type == "on" else "вимкнуть світло\\! ⚡"
    event_label = "Увімкнення" if type == "on" else "Вимкнення"
    time_info = "За графіком до кінця доби" if (type == "on" and end is None) else f"{escape_markdown_v2(format_time_display(start))} \\- {escape_markdown_v2(format_time_display(end))} \\({escape_markdown_v2(calculate_duration_from_min(start, end))}\\)"
    
    next_list = []
    for fev in future_events:
        if fev['start'] < 2880:
            next_list.append(f"👉 Вимкнення: {escape_markdown_v2(format_time_display(fev['start']))} \\- {escape_markdown_v2(format_time_display(fev['end']))}")
    next_events_block = ("\n\n*Наступні:*\n" + "\n".join(next_list)) if next_list else ""

    msg = (
        f"{icon} *Увага\\! Менше ніж за {escape_markdown_v2(str(int(diff)))} хвилин {status}*\n\n"
        f"📅 {escape_markdown_v2(day)}, {escape_markdown_v2(cur_time)}\n"
        f"⏰ {event_label}: {time_info}"
        f"{next_events_block}\n\n"
        f"💡 _{escape_markdown_v2(get_legacy_tip(type))}_\n\n"
        f"📊 *Графік:* https://mixaua\\.github\\.io/Mykolayivka/"
    )
    send_telegram_message(msg)
    print(f"✅ Технічне повідомлення ({event_label}) надіслано.")

# ============================================================
# --- ПОГОДА ---
# ============================================================

def get_wind_description(speed_kmh):
    """Інтерпретує швидкість вітру живою мовою."""
    if speed_kmh < 5:
        return "повний штиль"
    elif speed_kmh < 15:
        return "легкий вітерець"
    elif speed_kmh < 25:
        return "помірний вітер"
    elif speed_kmh < 40:
        return "вітряно"
    elif speed_kmh < 60:
        return "сильний вітер"
    else:
        return "шторм"

def get_weather_period_data(hourly_data, hours_range):
    """Витягує усереднені дані за заданий діапазон годин (індекси в масиві)."""
    start_idx, end_idx = hours_range
    temps = hourly_data['temperature_2m'][start_idx:end_idx]
    precip_prob = hourly_data['precipitation_probability'][start_idx:end_idx]
    precip = hourly_data['precipitation'][start_idx:end_idx]
    wind = hourly_data['windspeed_10m'][start_idx:end_idx]
    cloud = hourly_data['cloudcover'][start_idx:end_idx]
    codes = hourly_data['weathercode'][start_idx:end_idx]

    avg_temp = round(sum(temps) / len(temps)) if temps else 0
    avg_precip_prob = round(sum(precip_prob) / len(precip_prob)) if precip_prob else 0
    total_precip = round(sum(precip), 1) if precip else 0
    avg_wind = round(sum(wind) / len(wind)) if wind else 0
    avg_cloud = round(sum(cloud) / len(cloud)) if cloud else 0

    # Домінуючий weathercode
    dominant_code = max(set(codes), key=codes.count) if codes else 0

    return {
        'temp': avg_temp,
        'precip_prob': avg_precip_prob,
        'precip_mm': total_precip,
        'wind_kmh': avg_wind,
        'wind_desc': get_wind_description(avg_wind),
        'cloudcover': avg_cloud,
        'weathercode': dominant_code,
    }

def fetch_weather_data():
    """Завантажує погодні дані з Open-Meteo."""
    print("🌤️ [WEATHER] Завантажуємо дані з Open-Meteo...")
    try:
        response = requests.get(WEATHER_API, timeout=15)
        if not response.ok:
            print(f"❌ [WEATHER] Open-Meteo відповів: {response.status_code}")
            return None
        data = response.json()
        print(f"✅ [WEATHER] Дані отримано. Доступно годин: {len(data.get('hourly', {}).get('temperature_2m', []))}")
        return data
    except Exception as e:
        print(f"❌ [WEATHER] Помилка запиту: {e}")
        return None

def get_hourly_index(day_offset, hour):
    """Повертає індекс у масиві hourly для заданого дня та години."""
    return day_offset * 24 + hour

def call_gemini_for_weather(prompt_text):
    """Викликає Gemini API для генерації живого тексту."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ [WEATHER] GEMINI_API_KEY не знайдено, використовуємо заглушку.")
        return None

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 300,
        }
    }
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            timeout=20
        )
        if not response.ok:
            print(f"❌ [WEATHER] Gemini відповів: {response.status_code} — {response.text[:200]}")
            return None
        result = response.json()
        # Безпечний розбір відповіді з перевіркою структури
        candidates = result.get('candidates', [])
        if not candidates:
            print(f"❌ [WEATHER] Gemini: порожній список candidates. Відповідь: {str(result)[:300]}")
            return None
        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        if not parts:
            print(f"❌ [WEATHER] Gemini: порожній список parts. Content: {str(content)[:300]}")
            return None
        text = parts[0].get('text', '').strip()
        if not text:
            print(f"❌ [WEATHER] Gemini повернув порожній текст.")
            return None
        print(f"✅ [WEATHER] Gemini згенерував текст ({len(text)} символів)")
        return text
    except Exception as e:
        print(f"❌ [WEATHER] Помилка Gemini: {e}")
        return None

def build_weather_prompt_current(period_name, data, date_str):
    """Промпт для поточного/денного повідомлення (ранок/полудень/вечір)."""
    temp_sign = "+" if data['temp'] > 0 else ""
    precip_note = ""
    if data['precip_prob'] > 60:
        precip_note = f"висока ймовірність опадів ({data['precip_prob']}%), очікується {data['precip_mm']} мм"
    elif data['precip_prob'] > 30:
        precip_note = f"можливі невеликі опади ({data['precip_prob']}%)"
    else:
        precip_note = "опадів не очікується"

    cloud_note = ""
    if data['cloudcover'] < 20:
        cloud_note = "ясне небо"
    elif data['cloudcover'] < 50:
        cloud_note = "невелика хмарність"
    elif data['cloudcover'] < 80:
        cloud_note = "хмарно"
    else:
        cloud_note = "суцільна хмарність"

    period_context = {
        "ранок": "Починається новий день. Люди прокидаються, збираються на роботу чи у двір. Розкажи яка погода зустрічає їх цього ранку.",
        "полудень": "Середина дня. Хтось на обіді, хтось в полі чи городі. Розкажи яка погода зараз на вулиці.",
        "вечір": "День добігає кінця. Люди повертаються додому, виходять на прогулянку. Розкажи яка погода надворі цього вечора.",
    }
    context = period_context.get(period_name, "")

    return f"""Ти — погодний помічник для невеликого українського села Миколаївка.
Напиши живе погодне повідомлення для Telegram. Час доби: {period_name}, дата: {date_str}.

{context}

Погодні дані:
- Температура: {temp_sign}{data['temp']}°
- Небо: {cloud_note}
- Вітер: {data['wind_desc']}
- Опади: {precip_note}

Вимоги до тексту:
- 2-3 речення живою природною українською мовою
- Обов'язково згадай що зараз {period_name} — органічно, без штампів
- Тон: теплий, людський, трохи розмовний — як сусід розповідає про погоду
- Температуру назви числом з градусом (наприклад, +3°)
- Вітер — ТІЛЬКИ словами: "{data['wind_desc']}", без цифр
- Небо та опади — описово, живою мовою, без технічних відсотків та цифр
- Без емодзі всередині тексту
- Без формальних привітань ("Доброго ранку", "Доброго дня" тощо)
- НЕ використовуй Markdown-розмітку: жодних зірочок, решіток, підкреслень — лише чистий текст"""

def build_weather_prompt_tomorrow(morning, afternoon, evening, date_str):
    """Промпт для прогнозу на завтра (три частини доби)."""
    def period_desc(d):
        temp_sign = "+" if d['temp'] > 0 else ""
        cloud = "ясно" if d['cloudcover'] < 30 else ("мінлива хмарність" if d['cloudcover'] < 70 else "хмарно")
        precip = f"можливий дощ" if d['precip_prob'] > 40 else "без опадів"
        return f"{temp_sign}{d['temp']}°, {cloud}, {d['wind_desc']}, {precip}"

    return f"""Ти — погодний помічник для невеликого українського села Миколаївка.
Напиши прогноз погоди на завтра ({date_str}) для Telegram.

Дані по частинах доби:
- Ранок: {period_desc(morning)}
- День: {period_desc(afternoon)}
- Вечір: {period_desc(evening)}

Вимоги:
- Три частини: ранок, день, вечір — по 1-2 речення кожна
- Жива природна українська мова, в міру офіційна, в міру тепла
- Температуру називай числом з градусом (наприклад, +8°)
- Вітер — ТІЛЬКИ словами, без цифр
- В кінці — одне коротке загальне речення про завтрашній день
- НЕ використовуй Markdown-розмітку: жодних зірочок, решіток, підкреслень — лише чистий текст
- Розділяй частини ТОЧНО так, як показано нижче — я парсю текст за цими мітками:

###РАНОК###
<текст про ранок>
###ДЕНЬ###
<текст про день>
###ВЕЧІР###
<текст про вечір>
###ПІДСУМОК###
<одне загальне речення>"""

def load_weather_state():
    """Завантажує стан погодних відправок з state.json."""
    state_path = 'scripts/state.json'
    state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except:
            pass
    return state

def save_weather_state(state):
    """Зберігає стан погодних відправок у state.json."""
    state_path = 'scripts/state.json'
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
        print("💾 [WEATHER] Стан збережено в state.json")
    except Exception as e:
        print(f"❌ [WEATHER] Помилка збереження стану: {e}")

def is_weather_sent(state, key):
    """Перевіряє, чи вже відправлено погодне повідомлення сьогодні."""
    today = datetime.now().strftime("%Y-%m-%d")
    full_key = f"weather_{key}_{today}"
    sent = state.get(full_key, False)
    if sent:
        print(f"⏭️ [WEATHER] Повідомлення '{key}' вже відправлено сьогодні ({today}), пропускаємо.")
    return sent

def mark_weather_sent(state, key):
    """Позначає погодне повідомлення як відправлене."""
    today = datetime.now().strftime("%Y-%m-%d")
    full_key = f"weather_{key}_{today}"
    state[full_key] = True
    print(f"🔖 [WEATHER] Позначено як відправлено: '{key}' за {today}")
    return state

def format_date_ua(dt):
    """Форматує дату у вигляді '09 квітня (четвер)'."""
    months = {1:"січня",2:"лютого",3:"березня",4:"квітня",5:"травня",
              6:"червня",7:"липня",8:"серпня",9:"вересня",10:"жовтня",
              11:"листопада",12:"грудня"}
    days = {0:"понеділок",1:"вівторок",2:"середа",3:"четвер",
            4:"п'ятниця",5:"субота",6:"неділя"}
    return f"{dt.day:02d} {months[dt.month]} \\({escape_markdown_v2(days[dt.weekday()])}\\)"

def send_weather_current(period_key, header_emoji, period_name, weather_data, day_offset, hour_start, hour_end):
    """Відправляє погодне повідомлення для поточного періоду доби."""
    print(f"\n🌤️ [WEATHER] Формуємо повідомлення: {period_name}")

    state = load_weather_state()
    if is_weather_sent(state, period_key):
        return

    hourly = weather_data.get('hourly', {})
    idx_start = get_hourly_index(day_offset, hour_start)
    idx_end = get_hourly_index(day_offset, hour_end)
    print(f"📊 [WEATHER] Беремо години {hour_start}:00-{hour_end}:00 (індекси {idx_start}-{idx_end})")

    period_data = get_weather_period_data(hourly, (idx_start, idx_end))
    print(f"📊 [WEATHER] Дані: t={period_data['temp']}°, вітер={period_data['wind_kmh']}км/г "
          f"({period_data['wind_desc']}), хмари={period_data['cloudcover']}%, "
          f"опади={period_data['precip_prob']}%")

    now = datetime.now()
    date_str_plain = now.strftime("%d.%m")
    prompt = build_weather_prompt_current(period_name, period_data, date_str_plain)
    ai_text = call_gemini_for_weather(prompt)

    if not ai_text:
        print("⚠️ [WEATHER] Gemini недоступний, формуємо fallback-текст.")
        temp_sign = "+" if period_data['temp'] > 0 else ""
        t = f"{temp_sign}{period_data['temp']}°"
        wind = period_data['wind_desc']
        cloud = period_data['cloudcover']
        precip = period_data['precip_prob']

        if cloud < 20:
            sky = "небо ясне"
        elif cloud < 50:
            sky = "хмарки є, але сонце пробивається"
        elif cloud < 80:
            sky = "хмарно"
        else:
            sky = "небо затягнуло хмарами"

        rain = ", можливий дощ" if precip > 40 else ""

        period_phrases = {
            "ранок":   f"Ранок у Миколаївці зустрічає {t}. На вулиці {sky}, {wind}{rain}.",
            "полудень": f"О півдні надворі {t}. {sky.capitalize()}, {wind}{rain}.",
            "вечір":   f"Вечоріє. Надворі {t}, {sky}, {wind}{rain}.",
        }
        ai_text = period_phrases.get(period_name,
            f"Зараз {t}, {sky}, {wind}{rain}."
        )

    date_ua = format_date_ua(now)
    time_str = escape_markdown_v2(now.strftime("%H:%M"))
    ai_escaped = escape_markdown_v2(ai_text)

    msg = (
        f"{header_emoji} *Погода в Миколаївці*\n\n"
        f"📅 {date_ua}, {time_str}\n\n"
        f"{ai_escaped}\n\n"
        f"📊 *Сайт:* https://mixaua\\.github\\.io/Mykolayivka/"
    )

    send_telegram_message(msg)
    print(f"✅ [WEATHER] Повідомлення '{period_name}' відправлено.")

    state = mark_weather_sent(state, period_key)
    save_weather_state(state)

def send_weather_tomorrow(weather_data):
    """Відправляє прогноз погоди на завтра (три частини доби)."""
    print(f"\n🔮 [WEATHER] Формуємо прогноз на завтра...")

    state = load_weather_state()
    if is_weather_sent(state, "tomorrow"):
        return

    hourly = weather_data.get('hourly', {})
    tomorrow = datetime.now() + timedelta(days=1)

    # Ранок завтра: 6-10
    morning_data = get_weather_period_data(hourly, (get_hourly_index(1, 6), get_hourly_index(1, 10)))
    # День завтра: 11-16
    afternoon_data = get_weather_period_data(hourly, (get_hourly_index(1, 11), get_hourly_index(1, 16)))
    # Вечір завтра: 17-21
    evening_data = get_weather_period_data(hourly, (get_hourly_index(1, 17), get_hourly_index(1, 21)))

    print(f"📊 [WEATHER] Завтра ранок: t={morning_data['temp']}°, вітер={morning_data['wind_desc']}, "
          f"опади={morning_data['precip_prob']}%")
    print(f"📊 [WEATHER] Завтра день: t={afternoon_data['temp']}°, вітер={afternoon_data['wind_desc']}, "
          f"опади={afternoon_data['precip_prob']}%")
    print(f"📊 [WEATHER] Завтра вечір: t={evening_data['temp']}°, вітер={evening_data['wind_desc']}, "
          f"опади={evening_data['precip_prob']}%")

    date_str_plain = tomorrow.strftime("%d.%m")
    prompt = build_weather_prompt_tomorrow(morning_data, afternoon_data, evening_data, date_str_plain)
    ai_text = call_gemini_for_weather(prompt)

    # Розбиваємо відповідь Gemini за мітками ###
    if ai_text:
        def extract_section(text, marker):
            pattern = rf'###{marker}###\s*(.*?)(?=###|\Z)'
            match = re.search(pattern, text, re.DOTALL)
            return match.group(1).strip() if match else ""

        morning_text = extract_section(ai_text, "РАНОК")
        afternoon_text = extract_section(ai_text, "ДЕНЬ")
        evening_text = extract_section(ai_text, "ВЕЧІР")
        summary_text = extract_section(ai_text, "ПІДСУМОК")

        print(f"📝 [WEATHER] Розібрано: ранок={len(morning_text)}с, день={len(afternoon_text)}с, "
              f"вечір={len(evening_text)}с, підсумок={len(summary_text)}с")

        # Якщо парсинг не спрацював (Gemini не дотримався формату) — fallback на абзаци
        if not morning_text and not afternoon_text:
            print("⚠️ [WEATHER] Мітки не знайдено, fallback на розбивку по абзацах")
            paragraphs = [p.strip() for p in ai_text.strip().split('\n') if p.strip()]
            morning_text = paragraphs[0] if len(paragraphs) > 0 else ""
            afternoon_text = paragraphs[1] if len(paragraphs) > 1 else ""
            evening_text = paragraphs[2] if len(paragraphs) > 2 else ""
            summary_text = paragraphs[3] if len(paragraphs) > 3 else ""
    else:
        def fallback(d):
            s = "+" if d['temp'] > 0 else ""
            return f"{s}{d['temp']}°, {d['wind_desc']}."
        morning_text = fallback(morning_data)
        afternoon_text = fallback(afternoon_data)
        evening_text = fallback(evening_data)
        summary_text = ""

    date_ua = format_date_ua(tomorrow)
    now = datetime.now()
    time_str = escape_markdown_v2(now.strftime("%H:%M"))

    morning_temp = f"+{morning_data['temp']}°" if morning_data['temp'] > 0 else f"{morning_data['temp']}°"
    afternoon_temp = f"+{afternoon_data['temp']}°" if afternoon_data['temp'] > 0 else f"{afternoon_data['temp']}°"
    evening_temp = f"+{evening_data['temp']}°" if evening_data['temp'] > 0 else f"{evening_data['temp']}°"

    lines = [
        f"🗓️ *Прогноз на завтра — Миколаївка*\n\n",
        f"📅 {date_ua}, {time_str}\n\n",
        f"🌅 *Ранок* — {escape_markdown_v2(morning_temp)}\n{escape_markdown_v2(morning_text)}\n\n",
        f"☀️ *День* — {escape_markdown_v2(afternoon_temp)}\n{escape_markdown_v2(afternoon_text)}\n\n",
        f"🌆 *Вечір* — {escape_markdown_v2(evening_temp)}\n{escape_markdown_v2(evening_text)}\n",
    ]
    if summary_text:
        lines.append(f"\n_{escape_markdown_v2(summary_text)}_\n")
    lines.append(f"\n📊 *Сайт:* https://mixaua\\.github\\.io/Mykolayivka/")

    msg = "".join(lines)
    send_telegram_message(msg)
    print(f"✅ [WEATHER] Прогноз на завтра відправлено.")

    state = mark_weather_sent(state, "tomorrow")
    save_weather_state(state)

def run_weather_bot(now_h):
    """Головна логіка погодного блоку. Викликається з run_bot()."""
    print(f"\n{'='*40}")
    print(f"🌤️ [WEATHER] Перевірка погодного блоку. Година: {now_h}:xx")
    print(f"{'='*40}")

    weather_data = fetch_weather_data()
    if not weather_data:
        print("❌ [WEATHER] Не вдалося отримати дані погоди. Пропускаємо.")
        return

    if 4 <= now_h < 8:
        print("🌅 [WEATHER] Вікно: ранок (4-8). Відправляємо ранкову погоду.")
        send_weather_current("morning", "🌤️", "ранок", weather_data, 0, 6, 10)

    elif 10 <= now_h < 14:
        print("☀️ [WEATHER] Вікно: полудень (10-14). Відправляємо денну погоду.")
        send_weather_current("afternoon", "☀️", "полудень", weather_data, 0, 11, 16)

    elif 16 <= now_h < 18:
        print("🌆 [WEATHER] Вікно: вечір (16-18). Відправляємо вечірню погоду.")
        send_weather_current("evening", "🌇", "вечір", weather_data, 0, 17, 21)

    elif 18 <= now_h < 24:
        print("🔮 [WEATHER] Вікно: прогноз (18-24). Відправляємо прогноз на завтра.")
        send_weather_tomorrow(weather_data)

    else:
        print(f"😴 [WEATHER] Година {now_h} — поза погодними вікнами (4-8, 10-14, 16-18, 18-24).")

# ============================================================
# --- ЛОГІКА ЗАПУСКУ ---
# ============================================================

def run_bot():
    try:
        with open('database.json', 'r', encoding='utf-8') as f: data = json.load(f)
    except: return
    now = datetime.now()
    now_m = now.hour * 60 + now.minute
    current_time_str = now.strftime("%H:%M")
    days_ukr_cap = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "П'ятниця", 5: "Субота", 6: "Неділя"}
    days_ukr = {k: v.lower() for k, v in days_ukr_cap.items()}
    today_dow = now.weekday()

    print(f"🕒 [START] {current_time_str} ({days_ukr_cap[today_dow]}) | Хвилина дня: {now_m}")

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

    print("--- Події в графіку (merged) ---")
    for ev in merged:
        print(f"  - {format_time_display(ev['start'])} -> {format_time_display(ev['end'])}")
    print("--------------------------------")

    sent = False
    for i, ev in enumerate(merged):
        if ev['start'] <= now_m < ev['end']:
            diff = ev['end'] - now_m
            if 0 < diff <= 30:
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['end'], (merged[i+1]['start'] if i+1 < len(merged) else None), diff, "on", merged[i+1:])
                sent = True; break
            elif 70 < diff <= 90:
                quote = get_literature_tip("on")
                if quote: send_literature_notif(quote, "on"); sent = True; break
        elif ev['start'] > now_m:
            diff = ev['start'] - now_m
            if 0 < diff <= 30:
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['start'], ev['end'], diff, "off", merged[i+1:])
                sent = True; break
            elif 70 < diff <= 90:
                quote = get_literature_tip("off")
                if quote: send_literature_notif(quote, "off"); sent = True; break

    if not sent:
        print("😴 Умов для відправки графіка зараз немає.")

    # --- ПОГОДНИЙ БЛОК ---
    run_weather_bot(now.hour)

if __name__ == "__main__":
    run_bot()
