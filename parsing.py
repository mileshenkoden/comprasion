import os
import json
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Налаштування
CHROMEDRIVER_PATH = "/home/den/PycharmProjects/comparison/Driver/chromedriver"
DATA_FILE = "link/all_orders.json"
PROCESSED_FILE = "link/processed_links.json"
ALL_TEXTS_FILE = "all_texts.txt"
BLOCKED_SITES_FILE = "blocked_sait.json"
OUR_SITES_FILE = "our_sites.json"
RESULT_FILE = "result.json"

DOWNLOAD_FOLDER = os.path.abspath("downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/133.0.0.0")

prefs = {
    "download.default_directory": DOWNLOAD_FOLDER,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# Завантажуємо вже збережені посилання
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        all_a_order = json.load(file)
else:
    all_a_order = {}

if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE, "r", encoding="utf-8") as file:
        processed_links = set(json.load(file))
else:
    processed_links = set()

MAX_RETRIES = 3
RETRY_DELAY = 10

# Перебір збережених посилань
for count, (link_name, link_href) in enumerate(all_a_order.items(), start=1):
    print(f"[{count}/{len(all_a_order)}] Перехід на сторінку: {link_href}")

    if link_href in processed_links:
        print(f"Пропущено (вже оброблено): {link_href}")
        continue

    retries = 0
    while retries < MAX_RETRIES:
        try:
            if not link_href.startswith("http"):
                print(f"Помилка у посиланні: {link_href}")
                retries += 1
                continue

            try:
                response = requests.get(link_href, timeout=5)
                if response.status_code != 200:
                    print(f"Недоступний сайт: {link_href} (код {response.status_code})")
                    retries += 1
                    continue
            except requests.RequestException as e:
                print(f"Помилка підключення до {link_href}: {e}")
                retries += 1
                continue

            driver.get(link_href)
            driver.set_page_load_timeout(300)
            time.sleep(random.randint(10, 15))
            break  # Вихід з циклу при успішному відкритті сторінки

        except TimeoutException:
            retries += 1
            print(f"Помилка тайм-ауту при переході на {link_href} (спроба {retries}/{MAX_RETRIES})")
            if retries < MAX_RETRIES:
                print(f"Повторна спроба через {RETRY_DELAY} секунд...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Пропущено після {MAX_RETRIES} спроб: {link_href}")
                processed_links.add(link_href)
                continue

    try:
        download_button = driver.find_element(By.XPATH, "//a[contains(@class, 'btn-light') and contains(@download, '.txt')]")
        file_url = download_button.get_attribute("href")
        file_name = download_button.get_attribute("download")

        if not file_url or not file_name.endswith(".txt"):
            raise ValueError("Некоректне посилання або ім'я файлу.")

        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

        if os.path.exists(file_path):
            print(f"Файл {file_name} вже існує, пропускаємо.")
        else:
            print(f"Завантаження: {file_name} ({file_url})")
            driver.get(file_url)

        processed_links.add(link_href)

        with open(PROCESSED_FILE, "w", encoding="utf-8") as file:
            json.dump(list(processed_links), file, indent=4, ensure_ascii=False)

        time.sleep(random.randint(10, 15))

    except NoSuchElementException:
        print(f"Кнопку завантаження TXT не знайдено на {link_href}.")
    except Exception as e:
        print(f"Помилка при обробці {link_href}: {e}")

# Закриття браузера
driver.quit()
print("Скрипт завершено!")

# Обробка завантажених файлів
all_text = []
for filename in os.listdir(DOWNLOAD_FOLDER):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            words = content.split()
            all_text.extend(words)

with open(BLOCKED_SITES_FILE, "w", encoding="utf-8") as file:
    json.dump(all_text, file, indent=4, ensure_ascii=False)

# Порівняння списків blocked_sait.json та our_sites.json
if os.path.exists(BLOCKED_SITES_FILE) and os.path.exists(OUR_SITES_FILE):
    with open(BLOCKED_SITES_FILE, "r", encoding="utf-8") as f1, open(OUR_SITES_FILE, "r", encoding="utf-8") as f2:
        list1 = json.load(f1)
        list2 = json.load(f2)

    common_words = list(set(list1) & set(list2))

    with open(RESULT_FILE, "w", encoding="utf-8") as file:
        json.dump(common_words, file, indent=4, ensure_ascii=False)

    print("Результат збережено у result.json")

