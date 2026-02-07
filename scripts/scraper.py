import cloudscraper
import sys

def test_single_queue():
    # Використовуємо налаштування мобільного браузера
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android',
            'mobile': True
        }
    )
    
    q = "6.2"
    url = f"https://sumy.energy-ua.info/cherga/6-2"
    
    print(f"📡 Спроба отримати чергу {q}...")
    
    try:
        response = scraper.get(url, timeout=20)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 ПЕРЕМОГА! Сайт впустив телефон.")
            if "періоди відключень" in response.text.lower():
                print("✅ Дані на сторінці є.")
            else:
                print("❓ Сторінка порожня або інша структура.")
        else:
            print(f"❌ Відмова. Сайт все ще бачить бота.")
            
    except Exception as e:
        print(f"⚠️ Помилка з'єднання: {e}")

if __name__ == "__main__":
    test_single_queue()
