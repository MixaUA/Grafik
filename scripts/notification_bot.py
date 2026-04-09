import json
from datetime import datetime, timedelta
import os
import requests
import re
import random
import time  # 🆕 Додано імпорт для пауз

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

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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

def get_weather_label(weathercode):
    if weathercode == 0: return "ясно"
    elif weathercode == 1: return "переважно ясно"
    elif weathercode == 2: return "мінлива хмарність"
    elif weathercode == 3: return "хмарно"
    elif weathercode in (45, 48): return "туман"
    elif weathercode in (51, 53, 55): return "мряка"
    elif weathercode in (56, 57): return "крижана мряка"
    elif weathercode in (61, 80): return "невеликий дощ"
    elif weathercode in (63, 81): return "дощ"
    elif weathercode in (65, 82): return "сильний дощ"
    elif weathercode in (71, 85): return "невеликий сніг"
    elif weathercode in (73, 86): return "сніг"
    elif weathercode == 75: return "сильний сніг"
    elif weathercode == 77: return "снігова крупа"
    elif weathercode == 95: return "гроза"
    elif weathercode in (96, 99): return "гроза з градом"
    else: return "мінлива погода"

def format_groups_as_timeline(groups):
    lines = []
    for g in groups:
        h_start = f"{g['hour']:02d}:00"
        h_end   = f"{g['hour_end'] % 24:02d}:00"
        t_str   = f"+{g['temp']}°" if g['temp'] > 0 else f"{g['temp']}°"
        icon    = get_weather_icon(g['code'], g['cloud'])
        label   = get_weather_label(g['code'])
        wind    = get_wind_description(g['wind'])
        lines.append(f"🕐 {h_start}–{h_end}\n{icon} {label}, {t_str}, {wind}")
    return lines

def fetch_weather_data():
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
    return day_offset * 24 + hour

# 🆕 ЗМІНА: Функція Gemini з повторними спробами (Retry Logic)
def call_gemini_for_weather(prompt_text):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ [WEATHER] GEMINI_API_KEY не знайдено, використовуємо заглушку.")
        return None

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 500,
        }
    }

    max_retries = 3  # Кількість спроб
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload,
                timeout=25  # Трохи збільшив таймаут для стабільності
            )

            if response.status_code == 200:
                result = response.json()
                candidates = result.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        text = parts[0].get('text', '').strip()
                        if text:
                            print(f"✅ [WEATHER] Gemini згенерував текст з {attempt + 1}-ї спроби ({len(text)} символів).")
                            return text
            
            elif response.status_code == 503:
                print(f"⏳ [WEATHER] Спроба {attempt + 1} невдала (503 - High Demand). Чекаю 5 секунд...")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
            else:
                # При інших помилках (наприклад, 400 або 401) немає сенсу повторювати
                print(f"❌ [WEATHER] Gemini помилка {response.status_code}: {response.text[:200]}")
                break 

        except Exception as e:
            print(f"❌ [WEATHER] Помилка запиту (спроба {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

    print("⚠️ [WEATHER] Всі спроби вичерпано, переходимо до fallback.")
    return None

# ============================================================
# --- ПРОМПТИ ---
# ============================================================

# 🆕 ЗМІНА: Більше свободи для Gemini + акцент на різких змінах температури!
def build_weather_summary_prompt(morning, afternoon, evening, date_str, day_word):
    def pd(d):
        s = "+" if d['temp'] > 0 else ""
        cloud = "ясно" if d['cloudcover'] < 30 else ("мінлива хмарність" if d['cloudcover'] < 70 else "хмарно")
        precip = "можливий дощ" if d['precip_prob'] > 40 else "без опадів"
        return f"{s}{d['temp']}°, {cloud}, {d['wind_desc']}, {precip}"

    # 🆕 Перевірка на різкі зміни температури
    temp_changes = []
    if abs(morning['temp'] - afternoon['temp']) >= 4:
        diff = afternoon['temp'] - morning['temp']
        temp_changes.append(f"температура {('підніметься' if diff > 0 else 'впаде')} на {abs(diff)}° вдень")
    if abs(afternoon['temp'] - evening['temp']) >= 4:
        diff = evening['temp'] - afternoon['temp']
        temp_changes.append(f"ввечері {('потеплішає' if diff > 0 else 'похолодає')} на {abs(diff)}°")

    temp_note = f"\n\n⚠️ ОСОБЛИВА УВАГА: {'; '.join(temp_changes)}" if temp_changes else ""

    return f"""Ти — погодний помічник для українського села Миколаївка.
Напиши живий підсумок про погоду {day_word} ({date_str}).

Дані:
- Ранок: {pd(morning)}
- День: {pd(afternoon)}
- Вечір: {pd(evening)}{temp_note}

📋 ПРАВИЛА:
1. 2-3 речення (не одне, а декілька!)
2. Додай практичну пораду: "візьміть парасольку", "одягайтеся тепліше", "ідеально для прогулянки", "вітер сильний — тримайте капелюхи"
3. Згадай особливості: хмарність, вітер, опади — не просто "буде дощ", а "дощ із вітром, тому парасолька може не врятувати"
4. 🆕 ЯКЩО Є РІЗКІ ЗМІНИ ТЕМПЕРАТУРИ (позначено ⚠️) — ОБОВ'ЯЗКОВО згадай про це і дай пораду!
5. Будь природним, розмовним, теплим — як сусід розповідає
6. Закінчуй крапкою, без Markdown
7. Не рахуй слова — пиши скільки треба для повноти

🚫 ЗАБОРОНЕНО:
- Не пиши вступних фраз: "Ось прогноз", "Звісно", "Тримайте", "Будь ласка", "На", "Пропоную", "Відповідь", "Результат"
- Пиши ОДРАЗУ текст прогнозу без жодних преамбул
- Не використовуй фрази на кшталт "як штучний інтелект" чи "я погодний помічник"

Приклад ХОРОШОЇ відповіді:
"Сьогодні хмарно з періодичним дощем, тому парасолька обов'язкова. Ввечері різко похолодає на 5 градусів — обов'язково одягайтеся тепліше! Загалом день не надто вдалий для прогулянок, але якщо вийдете — візьміть теплу куртку."

Напиши зараз:"""

def _fallback_summary(morning, afternoon, evening):
    has_rain = any(d['precip_prob'] > 40 for d in [morning, afternoon, evening])
    avg_cloud = round((morning['cloudcover'] + afternoon['cloudcover'] + evening['cloudcover']) / 3)
    if has_rain: return "День дощовий, варто взяти парасольку."
    elif avg_cloud < 30: return "День очікується ясний і сонячний."
    elif avg_cloud < 70: return "Хмарно, але без опадів."
    else: return "Похмурий день без суттєвих опадів."

def build_weather_prompt_current(period_name, data, date_str):
    temp_sign = "+" if data['temp'] > 0 else ""
    if data['precip_prob'] > 60:
        precip_note = f"висока ймовірність опадів ({data['precip_prob']}%), очікується {data['precip_mm']} мм"
    elif data['precip_prob'] > 30:
        precip_note = f"можливі невеликі опади ({data['precip_prob']}%)"
    else:
        precip_note = "опадів не очікується"

    if data['cloudcover'] < 20: cloud_note = "ясне небо"
    elif data['cloudcover'] < 50: cloud_note = "невелика хмарність"
    elif data['cloudcover'] < 80: cloud_note = "хмарно"
    else: cloud_note = "суцільна хмарність"

    period_context = {
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

# ============================================================
# --- СТАН ---
# ============================================================

def load_weather_state():
    state_path = 'scripts/state.json'
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ [WEATHER] Не вдалось прочитати state.json: {e}")
    return {}

def save_weather_state(state):
    state_path = 'scripts/state.json'
    try:
        existing = {}
        if os.path.exists(state_path):
            try:
                with open(state_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except:
                pass
        existing.update(state)
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=4)
        print("💾 [WEATHER] Стан збережено в state.json (існуючі ключі збережено)")
    except Exception as e:
        print(f"❌ [WEATHER] Помилка збереження стану: {e}")

def is_weather_sent(state, key):
    today = datetime.now().strftime("%Y-%m-%d")
    full_key = f"weather_{key}_{today}"
    sent = state.get(full_key, False)
    if sent:
        print(f"⏭️ [WEATHER] Повідомлення '{key}' вже відправлено сьогодні ({today}), пропускаємо.")
    return sent

def mark_weather_sent(state, key):
    today = datetime.now().strftime("%Y-%m-%d")
    full_key = f"weather_{key}_{today}"
    state[full_key] = True
    print(f"🔖 [WEATHER] Позначено як відправлено: '{key}' за {today}")
    return state

def format_date_ua(dt):
    months = {1:"січня",2:"лютого",3:"березня",4:"квітня",5:"травня",
              6:"червня",7:"липня",8:"серпня",9:"вересня",10:"жовтня",
              11:"листопада",12:"грудня"}
    days = {0:"понеділок",1:"вівторок",2:"середа",3:"четвер",
            4:"п'ятниця",5:"субота",6:"неділя"}
    return f"{dt.day:02d} {months[dt.month]} \\({escape_markdown_v2(days[dt.weekday()])}\\)"

# ============================================================
# --- ВІДПРАВНИКИ ПОГОДИ ---
# ============================================================

def _parse_three_sections(ai_text):
    """Розбирає відповідь Gemini за мітками ###РАНОК### ###ДЕНЬ### ###ВЕЧІР### ###ПІДСУМОК###."""
    
    # 🆕 Видаляємо вступні фрази Gemini
    ai_text = ai_text.strip()
    ai_text = re.sub(r'^(ось|звісно|тримайте|будь ласка|на|пропоную|відповідь|результат|готово|тримай)[:\s]+', '', ai_text, flags=re.IGNORECASE)
    ai_text = re.sub(r'^(як штучний інтелект|я погодний помічник|я з радістю|допоможу вам)[:\s]+', '', ai_text, flags=re.IGNORECASE)
    
    def extract_section(text, marker):
        pattern = rf'###{marker}###\s*(.*?)(?=###|\Z)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    morning_text   = extract_section(ai_text, "РАНОК")
    afternoon_text = extract_section(ai_text, "ДЕНЬ")
    evening_text   = extract_section(ai_text, "ВЕЧІР")
    summary_text   = extract_section(ai_text, "ПІДСУМОК")

    print(f"📝 [WEATHER] Розібрано: ранок={len(morning_text)}с, день={len(afternoon_text)}с, "
          f"вечір={len(evening_text)}с, підсумок={len(summary_text)}с")

    if not morning_text and not afternoon_text:
        print("⚠️ [WEATHER] Мітки не знайдено, fallback на розбивку по абзацах")
        paragraphs = [p.strip() for p in ai_text.strip().split('\n') if p.strip()]
        morning_text   = paragraphs[0] if len(paragraphs) > 0 else ""
        afternoon_text = paragraphs[1] if len(paragraphs) > 1 else ""
        evening_text   = paragraphs[2] if len(paragraphs) > 2 else ""
        summary_text   = paragraphs[3] if len(paragraphs) > 3 else ""

    return morning_text, afternoon_text, evening_text, summary_text


def _fallback_three_sections(morning_data, afternoon_data, evening_data):
    def sky_desc(d):
        c = d['cloudcover']
        if c < 20:   return "небо ясне"
        elif c < 50: return "хмарки є, але сонце пробивається"
        elif c < 80: return "хмарно"
        else:        return "небо затягнуло хмарами"

    def rain_note(d):
        return ", можливий дощ" if d['precip_prob'] > 40 else ""

    def fmt(d):
        s = "+" if d['temp'] > 0 else ""
        return f"{s}{d['temp']}°"

    morning_text   = (f"Надворі {fmt(morning_data)}, {sky_desc(morning_data)}, "
                      f"{morning_data['wind_desc']}{rain_note(morning_data)}.")
    afternoon_text = (f"Удень температура {fmt(afternoon_data)}, {sky_desc(afternoon_data)}, "
                      f"{afternoon_data['wind_desc']}{rain_note(afternoon_data)}.")
    evening_text   = (f"Увечері {fmt(evening_data)}, {sky_desc(evening_data)}, "
                      f"{evening_data['wind_desc']}{rain_note(evening_data)}.")
    summary_text   = ""
    return morning_text, afternoon_text, evening_text, summary_text


def _build_three_section_message(header_emoji, title_str, date_ua, time_str,
                                  morning_data, afternoon_data, evening_data,
                                  morning_text, afternoon_text, evening_text,
                                  summary_text):
    m_icon = get_weather_icon(morning_data['weathercode'],   morning_data['cloudcover'])
    a_icon = get_weather_icon(afternoon_data['weathercode'], afternoon_data['cloudcover'])
    e_icon = get_weather_icon(evening_data['weathercode'],   evening_data['cloudcover'])

    lines = [
        f"{header_emoji} *{escape_markdown_v2(title_str)}*\n\n",
        f"📅 {date_ua}\n",
        f"🕐 {time_str}\n\n",
        f"{m_icon} *Ранок*\n{escape_markdown_v2(morning_text)}\n\n",
        f"{a_icon} *День*\n{escape_markdown_v2(afternoon_text)}\n\n",
        f"{e_icon} *Вечір*\n{escape_markdown_v2(evening_text)}\n",
    ]
    if summary_text:
        lines.append(f"\n_{escape_markdown_v2(summary_text)}_\n")
    lines.append(f"\n📊 *Сайт:* https://mixaua\\.github\\.io/Mykolayivka/")
    return "".join(lines)


def _temp_str(d):
    return f"+{d['temp']}°" if d['temp'] > 0 else f"{d['temp']}°"

def get_weather_icon(weathercode, cloudcover=50):
    if weathercode == 0: return "☀️"
    elif weathercode in (1, 2): return "🌤️" if cloudcover < 50 else "⛅"
    elif weathercode == 3: return "☁️"
    elif weathercode in (45, 48): return "🌫️"
    elif weathercode in (51, 53, 55, 56, 57): return "🌦️"
    elif weathercode in (61, 63, 65, 80, 81, 82): return "🌧️"
    elif weathercode in (71, 73, 75, 77, 85, 86): return "🌨️"
    elif weathercode in (95, 96, 99): return "⛈️"
    else: return "🌡️"


# ============================================================
# --- ЗБЕРЕЖЕННЯ ТА ПОРІВНЯННЯ ПРОГНОЗІВ ---
# ============================================================

def save_forecast_snapshot(date_str, timeline_groups):
    state = load_weather_state()
    key   = f"forecast_{date_str}"
    state[key] = timeline_groups
    save_weather_state(state)
    print(f"💾 [FORECAST] Збережено прогноз для {date_str} ({len(timeline_groups)} груп)")

def load_forecast_snapshot(date_str):
    state = load_weather_state()
    return state.get(f"forecast_{date_str}")

def build_timeline_groups(hourly_data, day_offset, hour_from, hour_to):
    hours = list(range(hour_from, hour_to))
    raw = []
    for h in hours:
        idx   = get_hourly_index(day_offset, h)
        raw.append({
            'hour':  h,
            'code':  hourly_data['weathercode'][idx],
            'temp':  round(hourly_data['temperature_2m'][idx]),
            'wind':  round(hourly_data['windspeed_10m'][idx]),
            'cloud': round(hourly_data['cloudcover'][idx]),
        })

    if not raw: return []

    groups = []
    cur = dict(raw[0])
    cur['hour_end'] = cur['hour'] + 1
    for r in raw[1:]:
        if r['code'] == cur['code']:
            cur['temp']     = round((cur['temp']  + r['temp'])  / 2)
            cur['wind']     = round((cur['wind']  + r['wind'])  / 2)
            cur['cloud']    = round((cur['cloud'] + r['cloud']) / 2)
            cur['hour_end'] = r['hour'] + 1
        else:
            groups.append(cur)
            cur = dict(r)
            cur['hour_end'] = cur['hour'] + 1
    groups.append(cur)
    return groups

def compare_forecasts(old_groups, new_groups):
    changes = []
    def expand(groups):
        hours = {}
        for g in groups:
            for h in range(g['hour'], g['hour_end']):
                hours[h] = g
        return hours

    old_map = expand(old_groups)
    new_map = expand(new_groups)
    all_hours = sorted(set(old_map) | set(new_map))
    processed = set()

    for h in all_hours:
        if h in processed: continue
        og = old_map.get(h)
        ng = new_map.get(h)
        if not og or not ng: continue

        code_changed = og['code'] != ng['code']
        temp_changed = abs(og['temp'] - ng['temp']) >= 3

        if code_changed or temp_changed:
            h_end = h + 1
            while h_end in all_hours:
                og2 = old_map.get(h_end)
                ng2 = new_map.get(h_end)
                if not og2 or not ng2: break
                if og2['code'] == og['code'] and ng2['code'] == ng['code']:
                    h_end += 1
                else:
                    break

            for hh in range(h, h_end): processed.add(hh)

            time_str = f"{h:02d}:00–{h_end % 24:02d}:00"
            old_t = f"+{og['temp']}°" if og['temp'] > 0 else f"{og['temp']}°"
            new_t = f"+{ng['temp']}°" if ng['temp'] > 0 else f"{ng['temp']}°"
            old_icon = get_weather_icon(og['code'], og['cloud'])
            new_icon = get_weather_icon(ng['code'], ng['cloud'])
            old_label = get_weather_label(og['code'])
            new_label = get_weather_label(ng['code'])

            changes.append({
                'time': time_str,
                'old':  f"{old_icon} {old_label}, {old_t}",
                'new':  f"{new_icon} {new_label}, {new_t}",
            })
    return changes

def build_changes_prompt(changes, date_str):
    changes_text = "\n".join(
        f"- {c['time']}: було {c['old']} → стало {c['new']}" for c in changes
    )
    return f"""Ти — погодний помічник для українського села Миколаївка.
Прогноз на {date_str} змінився порівняно з вчорашнім.

Зміни:
{changes_text}

📋 ПРАВИЛА:
- Напиши 1-2 речення (не одне!)
- ОБОВ'ЯЗКОВО закінчуй крапкою, НЕ комою!
- Тон — спокійний, інформативний, без паніки
- Додай пораду або коментар
- Без Markdown, без емодзі, лише чистий текст
- Перевір що речення завершене!"""


# 🆕 ЗМІНА 2: Функція send_weather_today тепер приймає час запуску
def send_weather_today(weather_data, now_h, now_m):
    """
    Ранкове повідомлення: таймлайн від ПОТОЧНОГО часу до 22:00.
    Якщо затримка — починаємо з наступної повної години.
    """
    print(f"\n🌅 [WEATHER] Формуємо прогноз на сьогодні (Запуск о {now_h}:{now_m})...")

    state = load_weather_state()
    if is_weather_sent(state, "day_report"):
        return

    hourly   = weather_data.get('hourly', {})
    now      = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # 🆕 Логіка динамічного старту
    if now_h < 6:
        start_hour = 6
    else:
        start_hour = now_h + 1 if now_m > 0 else now_h
    
    if start_hour >= 22:
        print(f"⚠️ [WEATHER] Занадто пізно для денного звіту (зараз {now_h}:{now_m}). Пропускаємо.")
        return

    print(f"📊 [WEATHER] Таймлайн на сьогодні: {start_hour:02d}:00 – 22:00")

    groups   = build_timeline_groups(hourly, 0, start_hour, 22)
    timeline = format_groups_as_timeline(groups)

    morning_data   = get_weather_period_data(hourly, (get_hourly_index(0, 6),  get_hourly_index(0, 10)))
    afternoon_data = get_weather_period_data(hourly, (get_hourly_index(0, 11), get_hourly_index(0, 16)))
    evening_data   = get_weather_period_data(hourly, (get_hourly_index(0, 17), get_hourly_index(0, 21)))

    summary_text = call_gemini_for_weather(
        build_weather_summary_prompt(morning_data, afternoon_data, evening_data,
                                     now.strftime("%d.%m"), "сьогодні")
    )
    
    # 🆕 ВАЛІДАЦІЯ ТА ОБРОБКА ВІДПОВІДІ GEMINI
    final_summary = ""
    if summary_text:
        # Очищаємо текст
        summary_text = summary_text.strip()
        
        # Перевіряємо на обрізання (закінчується на кому)
        if summary_text.rstrip().endswith(','):
            print(f"⚠️ [WEATHER] Gemini обрізав текст (закінчується на кому): '{summary_text}'")
            # Прибираємо кому і додаємо крапку
            summary_text = summary_text.rstrip().rstrip(',') + '.'
        
        # Перевіряємо довжину
        if len(summary_text) < 30:  # 🆕 Збільшили мінімум (бо тепер 2-3 речення)
            print(f"⚠️ [WEATHER] Текст занадто короткий ({len(summary_text)}с), використовуємо fallback")
            final_summary = _fallback_summary(morning_data, afternoon_data, evening_data)
        else:
            # Перевіряємо чи закінчується на крапку
            if not summary_text.endswith('.'):
                print(f"⚠️ [WEATHER] Текст не закінчується крапкою, додаємо")
                summary_text = summary_text.rstrip() + '.'
            final_summary = summary_text
            print(f"✅ [WEATHER] Прийнято summary: '{final_summary}'")
    else:
        print(f"⚠️ [WEATHER] Gemini не повернув текст, використовуємо fallback")
        final_summary = _fallback_summary(morning_data, afternoon_data, evening_data)

    # --- Порівняння з вчорашнім прогнозом ---
    old_groups = load_forecast_snapshot(today_str)
    changes    = compare_forecasts(old_groups, groups) if old_groups else []

    if changes:
        print(f"🔄 [FORECAST] Знайдено {len(changes)} змін порівняно з вчорашнім прогнозом")
    else:
        print(f"✅ [FORECAST] Прогноз збігається з вчорашнім або збереженого немає")

    # Підмічаємо змінені блоки у таймлайні
    changed_hours = set()
    for c in changes:
        h_start = int(c['time'].split(':')[0])
        h_end   = int(c['time'].split('–')[1].split(':')[0])
        for h in range(h_start, h_end if h_end > h_start else h_end + 24):
            changed_hours.add(h)

    timeline_lines = []
    for block in timeline:
        hour_in_block = int(block.split(':')[0].replace('🕐 ', ''))
        prefix = "🔄 " if hour_in_block in changed_hours else ""
        timeline_lines.append(f"{prefix}{block}")

    timeline_block = "\n\n".join(escape_markdown_v2(b) for b in timeline_lines)

    # Речення про зміни від Gemini
    changes_line = ""
    if changes:
        changes_text = call_gemini_for_weather(
            build_changes_prompt(changes, now.strftime("%d.%m"))
        ) or f"Прогноз підкоригувався у {len(changes)} період(ах)."
        
        # 🆕 Валідація тексту змін
        if changes_text:
            changes_text = changes_text.strip()
            if changes_text.endswith(','):
                changes_text = changes_text.rstrip(',') + '.'
            if not changes_text.endswith('.'):
                changes_text = changes_text + '.'
            changes_line = f"🔄 _{escape_markdown_v2(changes_text)}_\n\n"

    date_ua  = format_date_ua(now)
    time_str = escape_markdown_v2(now.strftime("%H:%M"))

    lines = [
        f"🌤️ *{escape_markdown_v2('Погода в Миколаївці на сьогодні')}*\n\n",
        f"📅 {date_ua}\n",
        f"🕙 {time_str}\n\n",
        f"{timeline_block}\n\n",
        f"_{escape_markdown_v2(final_summary)}_\n\n",
    ]
    if changes_line:
        lines.append(changes_line)
    lines.append(f"📊 *Сайт:* https://mixaua\\.github\\.io/Mykolayivka/")

    send_telegram_message("".join(lines))
    print(f"✅ [WEATHER] Ранковий прогноз на сьогодні відправлено.")

    # 🆕 Зберігаємо стан ТУТ (єдине місце!)
    state = mark_weather_sent(state, "day_report")
    save_weather_state(state)


# 🆕 ЗМІНА 3: Функція send_weather_tomorrow завжди показує повний завтрашній день
def send_weather_tomorrow(weather_data):
    """
    Вечірнє повідомлення: прогноз на завтра (6–22).
    Завжди повний день, незалежно від часу запуску.
    """
    print(f"\n🔮 [WEATHER] Формуємо прогноз на завтра...")

    state = load_weather_state()
    if is_weather_sent(state, "night_report"):
        return

    hourly    = weather_data.get('hourly', {})
    now       = datetime.now()
    tomorrow  = now + timedelta(days=1)
    tmrw_str  = tomorrow.strftime("%Y-%m-%d")

    start_hour = 6
    end_hour = 22
    print(f"📊 [WEATHER] Таймлайн на завтра ({tmrw_str}): {start_hour:02d}:00 – {end_hour:02d}:00")

    groups   = build_timeline_groups(hourly, 1, start_hour, end_hour)
    timeline = format_groups_as_timeline(groups)

    morning_data   = get_weather_period_data(hourly, (get_hourly_index(1, 6),  get_hourly_index(1, 10)))
    afternoon_data = get_weather_period_data(hourly, (get_hourly_index(1, 11), get_hourly_index(1, 16)))
    evening_data   = get_weather_period_data(hourly, (get_hourly_index(1, 17), get_hourly_index(1, 21)))

    summary_text = call_gemini_for_weather(
        build_weather_summary_prompt(morning_data, afternoon_data, evening_data,
                                     tomorrow.strftime("%d.%m"), "завтра")
    )
    
    # 🆕 ВАЛІДАЦІЯ ВІДПОВІДІ GEMINI
    final_summary = ""
    if summary_text:
        summary_text = summary_text.strip()
        
        if summary_text.rstrip().endswith(','):
            print(f"⚠️ [WEATHER] Gemini обрізав текст (закінчується на кому)")
            summary_text = summary_text.rstrip().rstrip(',') + '.'
        
        if len(summary_text) < 30:  # 🆕 Збільшили мінімум
            print(f"⚠️ [WEATHER] Текст занадто короткий ({len(summary_text)}с)")
            final_summary = _fallback_summary(morning_data, afternoon_data, evening_data)
        else:
            if not summary_text.endswith('.'):
                summary_text = summary_text.rstrip() + '.'
            final_summary = summary_text
            print(f"✅ [WEATHER] Прийнято summary: '{final_summary}'")
    else:
        final_summary = _fallback_summary(morning_data, afternoon_data, evening_data)

    save_forecast_snapshot(tmrw_str, groups)

    timeline_block = "\n\n".join(escape_markdown_v2(b) for b in timeline)

    lines = [
        f"🗓️ *{escape_markdown_v2('Прогноз на завтра — Миколаївка')}*\n\n",
        f"📅 {format_date_ua(tomorrow)}\n\n",
        f"{timeline_block}\n\n",
        f"_{escape_markdown_v2(final_summary)}_\n\n",
        f"📊 *Сайт:* https://mixaua\\.github\\.io/Mykolayivka/",
    ]

    send_telegram_message("".join(lines))
    print(f"✅ [WEATHER] Прогноз на завтра відправлено і збережено для порівняння.")

    # 🆕 Зберігаємо стан ТУТ (єдине місце!)
    state = mark_weather_sent(state, "night_report")
    save_weather_state(state)


# ============================================================
# --- ГОЛОВНИЙ ПОГОДНИЙ ДИСПЕТЧЕР ---
# ============================================================

# 🆕 ЗМІНА 4: Прибрано подвійне збереження стану
def run_weather_bot(now_h, now_m):
    """Головна логіка погодного блоку. Вікна: 04-18 та 18-24."""
    print(f"\n{'='*40}")
    print(f"🌤️ [WEATHER] Перевірка погодного блоку. Час: {now_h:02d}:{now_m:02d}")
    print(f"{'='*40}")

    weather_data = fetch_weather_data()
    if not weather_
        print("❌ [WEATHER] Не вдалося отримати дані погоди. Пропускаємо.")
        return

    state = load_weather_state()

    # === 🌞 DAY_REPORT: 04:00 – 18:00 ===
    if 4 <= now_h < 18:
        if not is_weather_sent(state, "day_report"):
            print("🌅 [WEATHER] Вікно day_report. Прогноз на ЗАЛИШОК СЬОГОДНІ.")
            send_weather_today(weather_data, now_h, now_m)
            # 🆕 Прибрано: state = mark_weather_sent... (вже є в send_weather_today)
        else:
            print("✅ [WEATHER] day_report вже відправлено сьогодні.")
    
    # === 🌙 NIGHT_REPORT: 18:00 – 24:00 ===
    elif 18 <= now_h < 24:
        if not is_weather_sent(state, "night_report"):
            print("🌙 [WEATHER] Вікно night_report. Прогноз на ЗАВТРА (повний день).")
            send_weather_tomorrow(weather_data)
            # 🆕 Прибрано: state = mark_weather_sent... (вже є в send_weather_tomorrow)
        else:
            print("✅ [WEATHER] night_report вже відправлено.")
    
    else:
        print(f"😴 [WEATHER] Година {now_h} — поза вікнами (00-04 тиша).")


# ============================================================
# --- ЛОГІКА ЗАПУСКУ ---
# ============================================================

def run_bot():
    try:
        with open('database.json', 'r', encoding='utf-8') as f: data = json.load(f)
    except: return
    now = datetime.now()
    now_h = now.hour
    now_m = now.minute
    now_m_total = now_h * 60 + now_m
    
    current_time_str = now.strftime("%H:%M")
    days_ukr_cap = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "П'ятниця", 5: "Субота", 6: "Неділя"}
    days_ukr = {k: v.lower() for k, v in days_ukr_cap.items()}
    today_dow = now.weekday()

    print(f"🕒 [START] {current_time_str} ({days_ukr_cap[today_dow]}) | Хвилина дня: {now_m_total}")

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
        if ev['start'] <= now_m_total < ev['end']:
            diff = ev['end'] - now_m_total
            if 0 < diff <= 30:
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['end'], (merged[i+1]['start'] if i+1 < len(merged) else None), diff, "on", merged[i+1:])
                sent = True; break
            elif 70 < diff <= 90:
                quote = get_literature_tip("on")
                if quote: send_literature_notif(quote, "on"); sent = True; break
        elif ev['start'] > now_m_total:
            diff = ev['start'] - now_m_total
            if 0 < diff <= 30:
                send_notif(current_time_str, days_ukr_cap[today_dow], ev['start'], ev['end'], diff, "off", merged[i+1:])
                sent = True; break
            elif 70 < diff <= 90:
                quote = get_literature_tip("off")
                if quote: send_literature_notif(quote, "off"); sent = True; break

    if not sent:
        print("😴 Умов для відправки графіка зараз немає.")

    # 🆕 ПОГОДНИЙ БЛОК (передаємо години та хвилини)
    run_weather_bot(now_h, now_m)

if __name__ == "__main__":
    run_bot()
