import os
import json
import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# Шлях до драйвера Chrome
CHROMEDRIVER_PATH = "/home/den/PycharmProjects/comparison/Driver/chromedriver"

# Файл для збереження результатів
DATA_FILE = "link/all_orders.json"

# Налаштування браузера
options = Options()
options.add_argument("--headless")  # Запуск без інтерфейсу
options.add_argument("--disable-blink-features=AutomationControlled")  # Приховуємо автоматизацію
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")

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

while True:
    # Отримуємо HTML сторінки
    soup = BeautifulSoup(driver.page_source, "lxml")

    # Знаходимо всі записи
    all_orders = soup.find_all("div", class_="px-3 pt-3 border-top ng-star-inserted")

    new_links = 0  # Лічильник нових записів

    for order in all_orders:
        a_tag = order.find("a")
        if a_tag:
            href_a = "https://cip.gov.ua" + a_tag.get("href")  # Додаємо базову URL
            name_a = a_tag.text.strip()

            # Перевіряємо, чи це посилання вже є в файлі
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

    # Рандомна затримка перед натисканням на кнопку
    delay = random.randint(15, 25)
    print(f"Очікування {delay} секунд перед переходом на наступну сторінку...")
    time.sleep(delay)

    # Шукаємо кнопку "Next"
    try:
        next_button = driver.find_element(By.XPATH, "//a[@aria-label='Next']")
        if "disabled" in next_button.get_attribute("class"):  # Перевіряємо, чи кнопка неактивна
            print("Досягнуто останньої сторінки!")
            break

        # Натискання на кнопку
        next_button.click()
        print("Перехід на наступну сторінку...")

        # Очікуємо, поки сторінка завантажиться
        time.sleep(5)

    except Exception as e:
        print("Не вдалося знайти кнопку 'Next' або сталася помилка:", e)
        break

# Завантаження кожної сторінки по `href` та збереження у `date`
os.makedirs("date", exist_ok=True)

for count, (link_name, link_href) in enumerate(all_a_order.items(), start=1):
    print(f"[{count}/{len(all_a_order)}] Завантаження: {link_href}")

    # Відкриваємо сторінку
    driver.get(link_href)

    # Чекаємо, щоб сторінка повністю завантажилась
    time.sleep(random.randint(5, 10))

    # Збереження сторінки у файл
    page_source = driver.page_source
    file_name = f"date/{count}.html"  # Імена файлів як номери

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(page_source)

    print(f"Сторінка збережена у {file_name}!")

    # Рандомна затримка перед наступним запитом
    delay = random.randint(10, 20)
    print(f"Очікування {delay} секунд перед наступним запитом...")
    time.sleep(delay)

# Закриваємо браузер
driver.quit()
print("Скрипт завершено!")
