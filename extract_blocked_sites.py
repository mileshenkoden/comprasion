import os
import json

def extract_blocked_sites(download_folder="downloads", output_file="blocked_sait.json"):
    all_words = []

    # Перебір усіх файлів у папці
    for filename in os.listdir(download_folder):
        file_path = os.path.join(download_folder, filename)

        # Перевірка, що це текстовий файл
        if os.path.isfile(file_path) and filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    words = content.split()
                    all_words.extend(words)
            except Exception as e:
                print(f"⚠️ Не вдалося прочитати {filename}: {e}")

    # Запис у JSON
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(all_words, json_file, indent=4, ensure_ascii=False)

    print(f"✅ Збережено {len(all_words)} слів у {output_file}")
extract_blocked_sites()