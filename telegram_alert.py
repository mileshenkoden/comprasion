import requests
import json

TOKEN = "7692114474:AAGkZlNJoVqabWI6Xe1K6JwMmplyMNE1gaQ"
CHAT_ID = "685062387"

def send_telegram_alert(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        print("✅ Повідомлення надіслано!")
    else:
        print("❌ Помилка при надсиланні повідомлення:", response.text)

if __name__ == "__main__":
    # Читаємо повідомлення з result.json
    with open("result.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Формуємо повідомлення
    message = "\n".join(data) if data else "Немає спільних заблокованих сайтів."

    # Надсилаємо
    send_telegram_alert(TOKEN, CHAT_ID, message)
