const API_URL = "database.json";
const WEATHER_API = "https://api.open-meteo.com/v1/forecast?latitude=50.2699&longitude=34.3961&daily=temperature_2m_max,temperature_2m_min,weathercode&hourly=weathercode&timezone=Europe/Kiev&forecast_days=2";
const DAYS_UA = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"];

const calendarSVG = `<svg viewBox="0 0 24 24"><path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11zM7 11h5v5H7z"/></svg>`;
const clockSVG = `<svg class="loader-clock" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="3s" repeatCount="indefinite"/></path></svg>`;
const powerOffSVG = `<svg class="icon-pwr" viewBox="0 0 24 24" fill="none" stroke="#ff6b6b" stroke-width="2.5"><path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z"/></svg>`;
const powerOnSVG = `<svg class="icon-pwr" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" stroke-width="2.5"><path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z"/></svg>`;
const weatherIcons = {
    sun: `<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g id="day"><g transform="translate(32,32)"><g class="am-weather-sun am-weather-sun-shiny am-weather-easing-ease-in-out"><g><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(45)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(90)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(135)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(180)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(225)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(270)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g><g transform="rotate(315)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,11)" x1="0" x2="0" y1="0" y2="6" /></g></g><circle cx="0" cy="0" fill="white" r="7" stroke="black" stroke-width="1.5"/></g></g></svg>`,
    cloudSun: `<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g id="cloudy-day-1"><g transform="translate(20,10)"><g transform="translate(0,16)"><g class="am-weather-sun"><g><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(45)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(90)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(135)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(180)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(225)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(270)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g><g transform="rotate(315)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" transform="translate(0,9)" x1="0" x2="0" y1="0" y2="3"/></g></g><circle cx="0" cy="0" fill="white" r="5" stroke="black" stroke-width="1.5"/></g><g><path d="M47.7,35.4c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3    c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-20,-11)"/></g></g></g></svg>`,
    cloud: `<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g id="cloudy"><g transform="translate(20,10)"><g class="am-weather-cloud-1"><path d="M47.7,35.4     c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3     c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-10,-8), scale(0.6)"/></g><g class="am-weather-cloud-2"><path d="M47.7,35.4     c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3     c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-20,-11)"/></g></g></g></svg>`,
    rain: `<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g id="rainy-5"><g transform="translate(20,10)"><g><path d="M47.7,35.4c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3    c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-20,-11)"/></g></g><g transform="translate(34,46), rotate(10)"><line class="am-weather-rain-1" fill="none" stroke="black" stroke-dasharray="4,7" stroke-linecap="round" stroke-width="2" transform="translate(-6,1)" x1="0" x2="0" y1="0" y2="8" /><line class="am-weather-rain-2" fill="none" stroke="black" stroke-dasharray="4,7" stroke-linecap="round" stroke-width="2" transform="translate(0,-1)" x1="0" x2="0" y1="0" y2="8" /></g></g></svg>`,
    snow: `<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><g id="snowy-5"><g transform="translate(20,10)"><g><path d="M47.7,35.4c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3    c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-20,-11)"/></g><g class="am-weather-snow-1"><g transform="translate(7,28)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.2" transform="translate(0,9), rotate(0)" x1="0" x2="0" y1="-2.5" y2="2.5" /><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1" transform="translate(0,9), rotate(45)" x1="0" x2="0" y1="-2.5" y2="2.5" /><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1" transform="translate(0,9), rotate(90)" x1="0" x2="0" y1="-2.5" y2="2.5" /><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1" transform="translate(0,9), rotate(135)" x1="0" x2="0" y1="-2.5" y2="2.5" /></g></g><g class="am-weather-snow-2"><g transform="translate(16,28)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.2" transform="translate(0,9), rotate(0)" x1="0" x2="0" y1="-2.5" y2="2.5" /><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1" transform="translate(0,9), rotate(45)" x1="0" x2="0" y1="-2.5" y2="2.5" /><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1" transform="translate(0,9), rotate(90)" x1="0" x2="0" y1="-2.5" y2="2.5" /><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1" transform="translate(0,9), rotate(135)" x1="0" x2="0" y1="-2.5" y2="2.5" /></g></g></g></g></svg>`,
    thunder: `<svg viewBox="0 0 64 64"><path d="M47.7,35.4c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-2,-11)"/><g transform="translate(18, 30) scale(1.3)"><polygon fill="black" stroke="none" points="14.3,-2.9 20.5,-2.9 16.4,4.3 20.3,4.3 11.5,14.6 14.9,6.9 11.1,6.9" /><animateTransform attributeName="transform" type="translate" values="0 0; 0 5; 0 0" dur="1s" repeatCount="indefinite" additive="sum"/></g><g transform="translate(26,40), rotate(10)"><line class="am-weather-rain-1" fill="none" stroke="black" stroke-dasharray="4,7" stroke-linecap="round" stroke-width="2" transform="translate(-6,1)" x1="0" x2="0" y1="0" y2="8" /><line class="am-weather-rain-2" fill="none" stroke="black" stroke-dasharray="4,7" stroke-linecap="round" stroke-width="2" transform="translate(0,-1)" x1="0" x2="0" y1="0" y2="8" /></g></svg>`,
    fog: `<svg viewBox="0 0 64 64"><path d="M47.7,35.4c0-4.6-3.7-8.2-8.2-8.2c-1,0-1.9,0.2-2.8,0.5c-0.3-3.4-3.1-6.2-6.6-6.2c-3.7,0-6.7,3-6.7,6.7c0,0.8,0.2,1.6,0.4,2.3    c-0.3-0.1-0.7-0.1-1-0.1c-3.7,0-6.7,3-6.7,6.7c0,3.6,2.9,6.6,6.5,6.7l17.2,0C44.2,43.3,47.7,39.8,47.7,35.4z" fill="white" stroke="black" stroke-linejoin="round" stroke-width="1.2" transform="translate(-2,-11)"/><g transform="translate(12, 45)"><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" x1="0" y1="0" x2="40" y2="0" stroke-dasharray="4,4"><animateTransform attributeName="transform" type="translate" values="0 0; 2 0; -2 0; 0 0" dur="3.5s" repeatCount="indefinite" additive="sum"/></line><line fill="none" stroke="black" stroke-linecap="round" stroke-width="1.5" x1="0" y1="8" x2="35" y2="8" stroke-dasharray="4,4"><animateTransform attributeName="transform" type="translate" values="0 0; -2 0; 2 0; 0 0" dur="4s" repeatCount="indefinite" additive="sum" begin="0.3s"/></line></g></svg>`
};

let db = null, curQ = localStorage.getItem('selectedQueue');
let dayIdx = 0, viewMode = 1;
let weatherData = null, timerData = null;
let clickedSlots = JSON.parse(localStorage.getItem('clickedSlots')) || {};

function updateStatusDot() {
    const statusDot = document.getElementById('status-dot');
    if (!statusDot) return;

    const cacheTime = parseInt(localStorage.getItem('db_cache_time'));
    if (!cacheTime) {
        statusDot.className = 'offline-dot';
        return;
    }

    const twentyMinutes = 20 * 60 * 1000;
    const isFresh = (Date.now() - cacheTime) < twentyMinutes;

    statusDot.className = isFresh ? 'online-dot' : 'offline-dot';
}

async function init() {
    document.getElementById('year').innerText = new Date().getFullYear();
    updateFlipTimer();

    // Cache-first logic
    const cachedDb = localStorage.getItem('db_cache');
    if (cachedDb) {
        db = JSON.parse(cachedDb);
        const updateTimeEl = document.getElementById('update-time');
        if (updateTimeEl && db.update_time) updateTimeEl.innerText = `Оновлено: ${db.update_time}`;
    }

    renderGrid();
    updateStatusDot();

    // Conditional initial fetch
    const cacheTime = parseInt(localStorage.getItem('db_cache_time')) || 0;
    // Перевіряємо не тільки наявність кешу, а й наявність даних черг
    const needsFetch = !db || !db.queues || (Date.now() - cacheTime > 20 * 60 * 1000);

    if (needsFetch) {
        await fetchData(); // Чекаємо завершення якщо кешу немає, він битий, або застарілий
    }

    // Тепер db точно є, можна рендерити
    if (curQ) selectQ(curQ);

    await fetchWeather();

    setInterval(updateFlipTimer, 1000);
    setInterval(() => {
        if (curQ && db) {
            calculateTimerData();
            render();
            updateStatusDot();
        }
    }, 60000);
    setInterval(async () => { if (curQ) await fetchData(); }, 1200000);
    setInterval(() => { fetchWeather(); }, 3600000);
}

async function fetchData() {
    const now = Date.now();
    try {
        const r = await fetch(`${API_URL}?t=${now}`);
        if (!r.ok) throw new Error('Network response was not ok');
        const freshDb = await r.json();

        db = freshDb;
        localStorage.setItem('db_cache', JSON.stringify(db));
        localStorage.setItem('db_cache_time', now.toString());

        const updateTimeEl = document.getElementById('update-time');
        if (updateTimeEl) updateTimeEl.innerText = `Оновлено: ${db.update_time}`;

        if (curQ) {
            calculateTimerData();
            render();
        }
        updateStatusDot();
    } catch (e) {
        console.log('Fetch failed, continuing with cached data.', e);

        // Якщо кеш порожній і fetch падає - показуємо помилку
        if (!db) {
            const statusEl = document.getElementById('update-time');
            if (statusEl) statusEl.innerText = 'Помилка завантаження даних';

            // Показуємо повідомлення в content-list якщо черга вибрана
            if (curQ) {
                const cl = document.getElementById('content-list');
                if (cl) {
                    cl.innerHTML = `<div class="no-actual">Не вдалося завантажити дані.<br>Перевірте підключення до інтернету.</div>`;
                    cl.classList.remove('hidden');
                }
            }
        }

        updateStatusDot();
    }
}

function calculateTimerData() {
    if (!db || !curQ || !db.queues || !db.queues[curQ]) return;
    const now = new Date();
    const todayDow = (now.getDay() + 6) % 7;
    const allEvents = [];
    for (let dayOffset = 0; dayOffset <= 1; dayOffset++) {
        const targetDow = (todayDow + dayOffset) % 7;
        const dayName = DAYS_UA[targetDow];
        const scheduleForDay = db.queues[curQ][dayName];
        if (!scheduleForDay || scheduleForDay.length === 0) continue;
        const slots = scheduleForDay.map(val => {
            const [s, e] = val.split('-').map(t => {
                const [h, m] = t.split(':').map(Number);
                return h * 60 + m;
            });
            return { start: s + (dayOffset * 1440), end: (e === 0 ? 1440 : e) + (dayOffset * 1440), type: 'off' };
        });
        let last = dayOffset * 1440;
        slots.sort((a, b) => a.start - b.start).forEach(s => {
            if (s.start > last) allEvents.push({ start: last, end: s.start, type: 'on' });
            allEvents.push(s);
            last = s.end;
        });
        if (last < (dayOffset + 1) * 1440) allEvents.push({ start: last, end: (dayOffset + 1) * 1440, type: 'on' });
    }
    const nowM = now.getHours() * 60 + now.getMinutes();
    let cur = allEvents.find(ev => nowM >= ev.start && nowM < ev.end);
    if (cur && cur.end === 1440) {
        const nextSlot = allEvents.find(ev => ev.start === 1440);
        if (nextSlot && nextSlot.type === cur.type) { cur = { ...cur, end: nextSlot.end }; }
    }
    timerData = cur ? { endTime: cur.end, type: cur.type } : null;
}

function updateFlipTimer() {
    const cont = document.getElementById('timer-container');
    if (!cont) return;
    const now = new Date();
    let h, m, s, label;
    if (curQ && timerData) {
        const nowInSeconds = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
        let endInSeconds = timerData.endTime * 60;
        let diff = endInSeconds - nowInSeconds;
        if (diff >= 0) {
            h = Math.floor(diff / 3600); m = Math.floor((diff % 3600) / 60); s = diff % 60;
            label = timerData.type === 'off' ? "До ввімкнення:" : "До відключення:";
        } else { calculateTimerData(); return; }
    } else { h = now.getHours(); m = now.getMinutes(); s = now.getSeconds(); label = "Поточний час:"; }
    if (!cont.querySelector('.flip-clock')) {
        cont.innerHTML = `<div class="timer-wrapper"><div class="timer-label"></div><div class="flip-clock">
            <div class="flip-unit"><div class="flip-pair"><div class="roll-digit-container"><div id="h1" class="roll-digit-strip"></div></div><div class="roll-digit-container"><div id="h2" class="roll-digit-strip"></div></div></div><div class="unit-desc">год</div></div>
            <div class="flip-unit"><div class="flip-pair"><div class="roll-digit-container"><div id="m1" class="roll-digit-strip"></div></div><div class="roll-digit-container"><div id="m2" class="roll-digit-strip"></div></div></div><div class="unit-desc">хв</div></div>
            <div class="flip-unit"><div class="flip-pair"><div class="roll-digit-container"><div id="s1" class="roll-digit-strip"></div></div><div class="roll-digit-container"><div id="s2" class="roll-digit-strip"></div></div></div><div class="unit-desc">сек</div></div>
        </div></div>`;
        ['h1', 'h2', 'm1', 'm2', 's1', 's2'].forEach(id => {
            document.getElementById(id).innerHTML = Array.from({ length: 10 }, (_, i) => `<div class="roll-num">${i}</div>`).join('');
        });
    }
    setDigit('h1', Math.floor(h / 10)); setDigit('h2', h % 10);
    setDigit('m1', Math.floor(m / 10)); setDigit('m2', m % 10);
    setDigit('s1', Math.floor(s / 10)); setDigit('s2', s % 10);
    const tL = cont.querySelector('.timer-label'); if (tL) tL.textContent = label;
    updateGridMarker();
}

function updateGridMarker() {
    if (dayIdx !== 0) {
        document.querySelectorAll('.hour-cell.current').forEach(el => { el.classList.remove('current'); el.querySelector('.current-dot')?.remove(); });
        return;
    }
    const h = new Date().getHours(), currentId = `hcell-${h}`;
    const active = document.querySelector('.hour-cell.current');
    if (active && active.id === currentId) return;
    if (active) { active.classList.remove('current'); active.querySelector('.current-dot')?.remove(); }
    const newActive = document.getElementById(currentId);
    if (newActive) {
        newActive.classList.add('current');
        if (!newActive.querySelector('.current-dot')) newActive.prepend(Object.assign(document.createElement('div'), { className: 'current-dot' }));
    }
}

function setDigit(id, v) { const s = document.getElementById(id); if (s) s.style.transform = `translateY(-${v * 52}px)`; }

function render() {
    if (!db || !curQ || !db.queues || !db.queues[curQ]) {
        const cl = document.getElementById('content-list');
        if (cl) cl.innerHTML = `<div class="no-actual">Дані завантажуються...</div>`;
        return;
    }
    const now = new Date();
    const nowM = now.getHours() * 60 + now.getMinutes();
    const todayDow = (now.getDay() + 6) % 7;
    const targetDow = (todayDow + dayIdx) % 7;
    const dayName = DAYS_UA[targetDow];
    const scheduleForDay = db.queues[curQ][dayName];
    const elT = document.getElementById('weatherToday'), elTom = document.getElementById('weatherTomorrow');
    if (weatherData && elT && elTom) {
        elT.innerHTML = `${getWeatherIcon(weatherData.today.code)} <span class="temp-range">${fmtTemp(weatherData.today.max)} / ${fmtTemp(weatherData.today.min)}</span>`;
        elTom.innerHTML = `${getWeatherIcon(weatherData.tomorrow.code)} <span class="temp-range">${fmtTemp(weatherData.tomorrow.max)} / ${fmtTemp(weatherData.tomorrow.min)}</span>`;
    }
    if (!scheduleForDay || scheduleForDay.length === 0) {
        const msg = `<div class="no-actual">Графік на ${dayIdx === 0 ? 'сьогодні' : 'завтра'} очікується</div>`;
        const cl = document.getElementById('content-list');
        const cv = document.getElementById('content-visual');
        if (cl) { cl.innerHTML = msg; cl.classList.toggle('hidden', viewMode !== 1); }
        if (cv) { const hg = document.getElementById('hours-grid'); if (hg) hg.innerHTML = msg; cv.classList.toggle('hidden', viewMode !== 2); }
        return;
    }
    const slots = scheduleForDay.map(val => {
        const [s, e] = val.split('-').map(t => { const [h, m] = t.split(':').map(Number); return h * 60 + m; });
        return { start: s, end: (e === 0 ? 1440 : e), type: 'off', raw: val };
    }).sort((a, b) => a.start - b.start);
    let full = [], last = 0;
    slots.forEach(s => {
        if (s.start > last) full.push({ start: last, end: s.start, type: 'on', raw: `${minToTime(last)}-${minToTime(s.start)}` });
        full.push(s); last = s.end;
    });
    if (last < 1440) full.push({ start: last, end: 1440, type: 'on', raw: `${minToTime(last)}-${minToTime(1440)}` });
    renderList(full, nowM, now);
    renderVisual(slots, nowM);
}

function renderList(full, nowM, now) {
    const cont = document.getElementById('content-list'); if (!cont) return;
    cont.classList.toggle('hidden', viewMode !== 1);
    const display = full.filter(ev => dayIdx === 0 ? ev.end > nowM : true);
    const d = new Date(); if (dayIdx === 1) d.setDate(d.getDate() + 1);
    const dateStr = d.toISOString().split('T')[0];
    cont.innerHTML = display.map(ev => {
        const s = minToTime(ev.start), e = minToTime(ev.end), dur = (ev.end - ev.start) / 60;
        const isCur = dayIdx === 0 && nowM >= ev.start && nowM < ev.end;
        const isLocked = dayIdx === 0 && (ev.start - nowM <= 60);
        const slotId = btoa(unescape(encodeURIComponent(`${dateStr}-${curQ}-${ev.raw || (s + e)}`))).replace(/=/g, '');
        const hasClicked = clickedSlots.hasOwnProperty(slotId);
        return `<div class="slot ${ev.type} ${isCur ? 'current' : ''}">
            <div class="time-box"><span class="time">${s}-${e}</span></div>
            <div class="slot-right">
                <span class="dur">${dur % 1 === 0 ? dur : dur.toFixed(1)} год/${ev.type === 'off' ? 'викл' : 'вкл'}</span>
                <div style="width:32px; display:flex; justify-content:center;">
                    ${isCur ? clockSVG : `<div class="calendar-btn ${isLocked ? 'disabled' : ''} ${hasClicked ? 'no-anim' : ''}" 
                        onclick="${isLocked ? '' : `handleCalendarClick('${s}-${e}', ${dayIdx === 0}, '${ev.type}', '${slotId}')`}">
                        ${calendarSVG}
                    </div>`}
                </div>
            </div>
        </div>`;
    }).join('') || `<div class="no-actual">На сьогодні все</div>`;
}

function renderVisual(slots, nowM) {
    const cont = document.getElementById('content-visual'); if (!cont) return;
    cont.classList.toggle('hidden', viewMode !== 2);
    const grid = document.getElementById('hours-grid');
    let html = '';
    for (let h = 0; h < 24; h++) {
        const hS = h * 60, hE = (h + 1) * 60;
        let type = 'on';
        for (const s of slots) if (s.start <= hS && s.end > hS) { type = 'off'; break; }
        const isCur = dayIdx === 0 && nowM >= hS && nowM < hE;
        html += `<div id="hcell-${h}" class="hour-cell ${type} ${isCur ? 'current' : ''}">
            ${isCur ? '<div class="current-dot"></div>' : ''}
            <div class="hour-time">${h.toString().padStart(2, '0')}:00<br>${((h + 1) % 24).toString().padStart(2, '0')}:00</div>
            ${type === 'off' ? powerOffSVG : powerOnSVG}
        </div>`;
    }
    grid.innerHTML = html;
}

function fmtTemp(t) { return t > 0 ? `+${t}°` : `${t}°`; }
function minToTime(m) { return `${Math.floor(m / 60 % 24).toString().padStart(2, '0')}:${(m % 60).toString().padStart(2, '0')}`; }
function getWeatherIcon(code) {
    if (code === 0) return weatherIcons.sun;
    if ([1, 2].includes(code)) return weatherIcons.cloudSun;
    if (code === 3) return weatherIcons.cloud;
    if ([45, 48].includes(code)) return weatherIcons.fog;
    if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return weatherIcons.rain;
    if ((code >= 71 && code <= 77) || [85, 86].includes(code)) return weatherIcons.snow;
    if (code >= 95) return weatherIcons.thunder;
    return weatherIcons.cloud;
}

function renderGrid() {
    const g = document.getElementById('grid');
    if (g) g.innerHTML = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]
        .map(q => `<button class="btn-q" onclick="selectQ('${q}')">${q}</button>`).join('');
}

function selectQ(q) {
    curQ = q; localStorage.setItem('selectedQueue', q);
    document.getElementById('grid').classList.add('hidden');
    document.getElementById('box').classList.remove('hidden');
    document.getElementById('title').innerText = `Черга ${q}`;
    calculateTimerData(); render();
}

function resetView() { localStorage.removeItem('selectedQueue'); location.reload(); }
function setDay(i) { dayIdx = i; document.getElementById('tabL').classList.toggle('active', i === 0); document.getElementById('tabR').classList.toggle('active', i === 1); render(); }
function setView(v) { viewMode = v; document.getElementById('view1').classList.toggle('active', v === 1); document.getElementById('view2').classList.toggle('active', v === 2); render(); }

async function fetchWeather() {
    try {
        const r = await fetch(WEATHER_API);
        if (!r.ok) throw new Error();
        const data = await r.json();
        function getDominantCode(dayIndex) {
            if (!data.hourly?.weathercode?.length) return data.daily?.weathercode?.[dayIndex] ?? 3;
            const startHour = 10, endHour = 16, dayOffset = dayIndex * 24;
            const dayCodes = data.hourly.weathercode.slice(dayOffset + startHour, dayOffset + endHour + 1);

            const counts = {};
            for (const code of dayCodes) { counts[code] = (counts[code] || 0) + 1; }

            // 1. Якщо є хоча б 2 години ідеального сонця (код 0)
            if ((counts[0] || 0) >= 2) return 0;

            // 2. Якщо сонця мало, але є хоча б 2 години легкої хмарності (коди 1, 2)
            if ((counts[1] || 0) + (counts[2] || 0) >= 2) return 2;

            // 3. Якщо нічого з вищого не підійшло — тоді вже виводимо хмари або щось інше, що домінує
            let maxCount = 0, dominantCode = dayCodes[0];
            for (const code in counts) {
                if (counts[code] > maxCount) { maxCount = counts[code]; dominantCode = parseInt(code); }
            }
            return dominantCode;
        }

        weatherData = {
            timestamp: Date.now(),
            today: { max: Math.round(data.daily.temperature_2m_max[0]), min: Math.round(data.daily.temperature_2m_min[0]), code: getDominantCode(0) },
            tomorrow: { max: Math.round(data.daily.temperature_2m_max[1]), min: Math.round(data.daily.temperature_2m_min[1]), code: getDominantCode(1) }
        };
        localStorage.setItem('weatherCache', JSON.stringify(weatherData));
        if (curQ) render();
    } catch (e) { const c = localStorage.getItem('weatherCache'); if (c) { weatherData = JSON.parse(c); if (curQ) render(); } }
}

function cleanOldClicks() {
    const now = Date.now();
    for (const k in clickedSlots) if (now - clickedSlots[k] > 172800000) delete clickedSlots[k];
    localStorage.setItem('clickedSlots', JSON.stringify(clickedSlots));
}

function handleCalendarClick(slot, isToday, type, slotId) {
    const act = () => { openGoogleCalendar(slot, isToday, type); clickedSlots[slotId] = Date.now(); localStorage.setItem('clickedSlots', JSON.stringify(clickedSlots)); render(); };
    clickedSlots[slotId] ? showCustomAlert(act) : act();
}

function showCustomAlert(cb) {
    let ov = document.getElementById('modalOverlay');
    if (!ov) {
        ov = document.createElement('div'); ov.id = 'modalOverlay'; ov.className = 'modal-overlay';
        ov.innerHTML = `<div class="modal-content"><div style="font-size:40px; margin-bottom:10px;">📅</div><h3 style="margin:0 0 10px; color:#222;">Вже у календарі?</h3><p style="margin:0; color:#666; font-size:14px;">Ви вже додавали цей слот. Перейти ще раз?</p><div class="modal-btns"><button class="btn-modal btn-go" id="modalGo">Перейти</button><button class="btn-modal btn-exit" id="modalExit">Вийти</button></div></div>`;
        document.body.appendChild(ov);
    }
    ov.classList.add('active');
    document.getElementById('modalGo').onclick = () => { cb(); ov.classList.remove('active'); };
    document.getElementById('modalExit').onclick = () => ov.classList.remove('active');
}

function openGoogleCalendar(slot, isToday, type) {
    const [sT, eT] = slot.split('-');
    const d = new Date(); if (!isToday) d.setDate(d.getDate() + 1);
    const iso = (t) => { const [h, m] = t.split(':').map(Number); const date = new Date(d); date.setHours(h, m, 0, 0); return date.toISOString().replace(/-|:|\.\d\d\d/g, ""); };
    const title = `Черга ${curQ}: ${type === 'off' ? 'Відключення' : 'Включення'} (${sT}-${eT})`;
    window.open(`https://www.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${iso(sT)}/${iso(eT)}&sf=true&output=xml`, '_blank');
}

function registerSW() {
    if (!('serviceWorker' in navigator)) return;

    // Автоматично перезавантажуємо сторінку, коли новий воркер активується
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
            window.location.reload();
            refreshing = true;
        }
    });

    navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' }).then(reg => {
        // ПЕРЕВІРКА: якщо оновлення вже завантажене і чекає (після F5)
        if (reg.waiting) {
            showUpdateBar(reg.waiting);
        }

        reg.addEventListener('updatefound', () => {
            const w = reg.installing;
            w.addEventListener('statechange', () => {
                if (w.state === 'installed' && navigator.serviceWorker.controller) {
                    showUpdateBar(w);
                }
            });
        });
    });
}

function showUpdateBar(w) {
    const bar = document.createElement('div'); bar.className = 'update-bar';
    bar.innerHTML = `<span>Доступна нова версія!</span><button id="update-button">Оновити</button>`;
    document.body.appendChild(bar);
    document.getElementById('update-button').onclick = () => {
        w.postMessage({ action: 'skipWaiting' });
        setTimeout(() => { localStorage.removeItem('weatherCache'); window.location.reload(true); }, 500);
    };
}

cleanOldClicks();
init();
registerSW();
