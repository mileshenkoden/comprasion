import os
import json
import time
import random
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from telegram_alert import send_telegram_alert
def find_common_words(json_file1, json_file2):
    # Зчитуємо файли JSON
    with open(json_file1, 'r', encoding='utf-8') as f1, open(json_file2, 'r', encoding='utf-8') as f2:
        list1 = json.load(f1)
        list2 = json.load(f2)

    # Використовуємо множини для швидкого порівняння
    common_words = list(set(list1) & set(list2))
    with open("result.json", "w") as file:
        json.dump(common_words, file, ensure_ascii=False, indent=4)

TOKEN = "7692114474:AAGkZlNJoVqabWI6Xe1K6JwMmplyMNE1gaQ"
CHAT_ID = "685062387"


# Шлях до драйвера Chrome
CHROMEDRIVER_PATH = "/home/den/PycharmProjects/comparison/Driver/chromedriver"

# Файл для збереження результатів
DATA_FILE = "link/all_orders.json"

# Папка для завантаження файлів
DOWNLOAD_FOLDER = os.path.abspath("downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Налаштування браузера для автоматичного завантаження файлів
options = Options()
options.add_argument("--headless")  # Запуск без інтерфейсу
options.add_argument("--disable-blink-features=AutomationControlled")  # Приховуємо автоматизацію
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")

# Вказуємо папку для завантаження файлів
prefs = {
    "download.default_directory": DOWNLOAD_FOLDER,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# Запуск ChromeDriver
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# Відкриваємо сторінку
url = "https://cip.gov.ua/ua/filter?tagId=60751"
driver.get(url)

# Очікування для завантаження контенту
time.sleep(5)

# Завантажуємо вже збережені посилання
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        all_a_order = json.load(file)
else:
    all_a_order = {}

PROCESSED_FILE = "link/processed_links.json"

if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE, "r", encoding="utf-8") as file:
        processed_links = set(json.load(file))
else:
    processed_links = set()

try:
    next_button = driver.find_element(By.XPATH, "//a[@aria-label='Next']")

    # Прокручуємо до кнопки
    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
    time.sleep(1)  # невелика затримка

    # Пробуємо натиснути через JavaScript
    driver.execute_script("arguments[0].click();", next_button)
    print("Перехід на першу сторінку...")
    time.sleep(random.randint(5, 10))

except Exception as e:
    print("⚠️ Не вдалося натиснути 'Next' або сталася помилка:", e.__class__.__name__)
    print("Пропускаємо перехід.")

while True:
    # Отримуємо всі посилання
    orders = driver.find_elements(By.XPATH, "//div[@class='px-3 pt-3 border-top ng-star-inserted']/a")

    new_links = 0

    for order in orders:
        href_a = order.get_attribute("href")
        if not href_a.startswith("http"):
            href_a = "https://cip.gov.ua" + href_a

        name_a = order.text.strip()

        # Перевіряємо, чи вже є у файлі
        if name_a not in all_a_order:
            all_a_order[name_a] = href_a
            new_links += 1

    # Якщо є нові посилання, зберігаємо у файл
    if new_links > 0:
        os.makedirs("link", exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(all_a_order, file, indent=4, ensure_ascii=False)

        print(f"Додано {new_links} нових посилань у {DATA_FILE}!")

    else:
        print("Немає нових посилань, пропускаємо збереження.")

    # Переходимо на наступну сторінку
    try:
        next_button = driver.find_element(By.XPATH, "//a[@aria-label='Next']")
        if "disabled" in next_button.get_attribute("class"):
            print("Досягнуто останньої сторінки!")
            break

        next_button.click()
        print("Перехід на наступну сторінку...")
        time.sleep(random.randint(5, 10))

    except Exception as e:
        print("Не вдалося знайти кнопку 'Next' або сталася помилка:", e)
        break

# Завантаження тільки .txt файлів
# Завантаження тільки .txt файлів
MAX_RETRIES = 3  # Максимальна кількість повторних спроб
RETRY_DELAY = 10  # Затримка між спробами (у секундах)

for count, (link_name, link_href) in enumerate(all_a_order.items(), start=1):
    print(f"[{count}/{len(all_a_order)}] Перехід на сторінку: {link_href}")

    # Пропускаємо, якщо посилання вже оброблено
    if link_href in processed_links:
        print(f"[{count}/{len(all_a_order)}] Пропущено (вже оброблено): {link_href}")
        continue

    retries = 0  # Лічильник спроб
    while retries < MAX_RETRIES:
        try:
            driver.get(link_href)
            driver.set_page_load_timeout(300)  # 5 хвилин
            time.sleep(random.randint(10, 15))  # Очікування для завантаження
            break  # Якщо сторінка завантажилася успішно, виходимо з циклу
        except (TimeoutError, urllib3.exceptions.ReadTimeoutError) as e:
            retries += 1
            print(f"Помилка тайм-ауту при переході на {link_href} (спроба {retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                print(f"Повторна спроба через {RETRY_DELAY} секунд...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Не вдалося завантажити {link_href} після {MAX_RETRIES} спроб. Пропускаємо.")
                processed_links.add(link_href)  # Позначаємо як оброблене, щоб не застрягнути
                break


    driver.get(link_href)
    driver.set_page_load_timeout(300)  # 5 хвилин

    time.sleep(random.randint(10, 15))

    try:
        # Шукаємо кнопку завантаження TXT-файлу
        download_button = driver.find_element(By.XPATH,
                                              "//a[contains(@class, 'btn-light') and contains(@download, '.txt')]")

        # Отримуємо посилання на файл
        file_url = download_button.get_attribute("href")
        file_name = download_button.get_attribute("download")

        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)  # ДОДАНО: Повний шлях до файлу

        # ДОДАНО: Перевіряємо, чи файл вже існує
        if os.path.exists(file_path):
            print(f"Файл {file_name} вже існує, пропускаємо завантаження.")
            processed_links.add(link_href)  # Все одно додаємо в список оброблених
            continue  # Пропускаємо завантаження

        if file_url and file_name.endswith(".txt"):
            print(f"Завантаження: {file_name} ({file_url})")


            driver.get(file_url)  # Відкриваємо посилання (файл автоматично збережеться)

            # Додаємо посилання в список оброблених після завантаження
            processed_links.add(link_href)

            # Зберігаємо оновлений список оброблених посилань
            with open(PROCESSED_FILE, "w", encoding="utf-8") as file:
                json.dump(list(processed_links), file, indent=4, ensure_ascii=False)

        if file_url and file_name.endswith(".txt"):
            print(f"Завантаження: {file_name} ({file_url})")

            driver.get(file_url)

            processed_links.add(link_href)
            with open(PROCESSED_FILE, "w", encoding="utf-8") as file:
                json.dump(list(processed_links), file, indent=4, ensure_ascii=False)

            time.sleep(random.randint(10, 15))





    except Exception as e:
        print(f"Не вдалося знайти кнопку TXT-завантаження на {link_href}: {e}")

from extract_blocked_sites import extract_blocked_sites
extract_blocked_sites()
find_common_words("blocked_sait.json", "our_sites.json")
# Читання результатів порівняння
with open("result.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Формуємо повідомлення
message = "\n".join(data) if data else "Немає спільних заблокованих сайтів."

# Надсилаємо
send_telegram_alert(TOKEN, CHAT_ID, message)

# Закриваємо браузер
driver.quit()
print("Скрипт завершено!")
