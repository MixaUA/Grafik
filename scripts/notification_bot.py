import json
from datetime import datetime
import os
import requests
import re
import random

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
    requests.post(url, json=payload)

def send_literature_notif(quote, event_type):
    on_greetings = [
        "Оце прокинувся подивитися, що там у нашому графіку. Бачу, що ще маю трохи часу, перш ніж бігти вмикати вам рубильники. Поки ми всі чекаємо, тримайте цікавинку, а я ще трішки подрімаю. Скоро почуємось!",
        "Тихо зазирнув у ваші плани... Світло вже на підході! Поки воно ще в дорозі, пропоную хвилинку для роздумів. Не сумуйте, скоро буде трішки світліше!",
        "Привіт! Перевірив систему — все за розкладом. До увімкнення ще є час, тож вирішив не приходити з порожніми руками. Ось вам літературна пауза від мене.",
        "Я тут на мить прокинувся... Бачу, ви теж чекаєте на вогники? Поки ми в одній команді очікування, тримайте дещо для натхнення. Повернусь, коли треба буде діяти!",
        "Мої датчики кажуть, що скоро буде світло! А поки я готуюся до старту, ось вам трохи поживи для розуму. Відпочивайте, я на зв'язку.",
        "Доброго дня! Провів невеликий моніторинг — світло до нас прийде незабаром. Поки ви чекаєте, ось вам дещо цікаве для душі. Я ще заскочу перед увімкненням!",
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
        "Привітання! Моніторив графік і помітив наближення відключення. Вирішив не чекати останньої хвилини та поділитися з вами чимось особливим. Тримайтеся!",
        "Зайшов перевірити стан справ — так, вимкнення на підході. Але це не привід сумувати! Ось вам дещо для натхнення перед темрявою. Повернусь ближче до події!",
        "Добридень! Переглянув розклад і бачу, що скоро світло піде відпочивати. Поки воно ще з нами, тримайте літературну паузу від мене. До зустрічі перед відключенням!"
    ]
    title = "💡 *Передчуття світла\\.\\.\\.*" if event_type == "on" else "🌙 *Вечірні роздуми\\.\\.\\.*"
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

# --- ЛОГІКА ЗАПУСКУ ---
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

    # ВІДНОВЛЕНИЙ ВИВІД ГРАФІКА В ЛОГИ
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

    if not sent: print("😴 Умов для відправки зараз немає.")

if __name__ == "__main__":
    run_bot()
