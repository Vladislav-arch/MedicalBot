import re

async def extract_id(info_string):
    # Використовуємо регулярний вираз для пошуку id в рядку
    if info_string:
        match = re.search(r'Id:\s+(\d+)', info_string)

        # Перевіряємо, чи вдалося знайти співпадіння
        if match:
            # Повертаємо знайдене id як ціле число
            return int(match.group(1))
        else:
            # Якщо id не знайдено, повертаємо None або можна викинути виключення
            return None


async def extract_name(text):
    # Використовуємо регулярний вираз для пошуку ім'я в тексті
    match = re.search(r'Ім`я•\s+([^\n]+)', text)

    # Перевіряємо, чи знайдено відповідний патерн
    if match:
        # Повертаємо знайдене ім'я
        return match.group(1).strip()
    else:
        # Якщо нічого не знайдено, повертаємо None
        return None