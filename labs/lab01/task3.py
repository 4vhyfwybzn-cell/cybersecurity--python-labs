import csv
import datetime
import hashlib
import json
import os


class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль або сіль не можуть бути порожніми!")

    if len(password) < 16:
        raise ValidationError(
            "Пароль занадто короткий для Варіанту 5 (мінімум 16 символів)!"
        )

    # Конкатенація пароля та солі перед процедурою хешування
    salted_password = password + salt
    return hashlib.sha3_256(salted_password.encode("utf-8")).hexdigest()


def log_event(func):

    def wrapper(*args, **kwargs):
        # Визначення імені користувача з позиційних або іменованих аргументів
        username = args[0] if args else kwargs.get("username", "unknown")
        try:
            result_bool = func(*args, **kwargs)
            status = "success" if result_bool else "failure"
        except Exception as e:
            # Логування типу винятку у разі виникнення системного збою
            status = f"failure ({type(e).__name__})"
            raise
        finally:
            # Створення директорії логів та формування шляху до файлу
            log_dir = os.path.join("labs", "lab01", "data")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "log.json")

            # Формування структури запису логу
            log_entry = {
                "event": "login",
                "user": username,
                "result": status,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "args": list(args),
                "kwargs": kwargs,
            }

            # Читання існуючих логів для запобігання перезапису даних
            logs = []
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []

            # Додавання нового запису та збереження файлу журналу
            logs.append(log_entry)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        return result_bool

    return wrapper


def create_user(username: str, password: str) -> tuple:
    salt = "00005"  # Персоналізована сіль
    hash_value = generate_hash(password, salt)
    return (username, hash_value)


def create_users(users_list: list):
    data_dir = os.path.join("labs", "lab01", "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "users.csv")

    # Запис структури облікових даних у файл
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["login", "hash_password"])  # Створення заголовків таблиці
        for user in users_list:
            username, pwd = user
            try:
                user_tuple = create_user(username, pwd)
                writer.writerow(user_tuple)
            except (ValueError, ValidationError) as e:
                print(f"Помилка реєстрації користувача {username}: {e}")


def read_users_db() -> list:
    csv_path = os.path.join("labs", "lab01", "data", "users.csv")
    users_db = []
    if not os.path.exists(csv_path):
        return users_db

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Пропуск технічного рядка заголовків
        for row in reader:
            if row:
                users_db.append(row)
    return users_db


@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError("Поля логіна та пароля не можуть бути порожніми!")

    users_db = read_users_db()
    salt = "00005"  # Сіль перевірки

    try:
        current_hash = generate_hash(password, salt)
    except ValidationError:
        return False

    # Лінійний пошук збігів у базі даних
    for db_user, db_hash in users_db:
        if db_user == username and db_hash == current_hash:
            return True
    return False


def run_task3_demo():
    print("\n--- Виконання Завдання 3 ---")

    # Список тестових користувачів
    test_users = [
        ("admin_cyber", "SuperSecurePassword2026!"),
        ("user_test", "ShortPwd1"),
        ("analyst_5", "QuantumEncryptionKey#5"),
    ]

    print("Реєстрація та запис користувачів у CSV...")
    create_users(test_users)

    print("\nЗчитування створеної бази користувачів з CSV:")
    db_data = read_users_db()
    for row in db_data:
        print(f"Логін: {row[0]:<15} | Хеш: {row[1]}")

    print("\nТестування автентифікації (Логування в JSON):")
    # Перевірка входу з коректними даними
    res1 = login("admin_cyber", "SuperSecurePassword2026!")
    print(f"Спроба для 'admin_cyber' (правильний): {res1}")

    # Перевірка стійкості до некоректного пароля
    res2 = login("admin_cyber", "WrongPassword123456789")
    print(f"Спроба для 'admin_cyber' (неправильний): {res2}")
