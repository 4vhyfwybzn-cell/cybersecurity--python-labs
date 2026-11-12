import json
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab03.database import get_connection, initialize_database

BASE_DIR = Path(__file__).resolve().parent
SEED_PATH = BASE_DIR / "data" / "seed.json"


def seed_database() -> None:
    """Заповнити базу початковими даними з JSON-файлу в межах однієї транзакції."""
    initialize_database()

    if not SEED_PATH.exists():
        print(f"Файл початкових даних не знайдено: {SEED_PATH}")
        return

    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    with closing(get_connection()) as connection:
        try:
            # Перевіряємо, чи є вже категорії в базі
            cursor = connection.execute("SELECT COUNT(*) FROM categories")
            categories_count = cursor.fetchone()[0]

            if categories_count > 0:
                print("База даних уже містить початкові дані. Пропускаємо заповнення.")
                return

            with connection:
                # Вставка категорій з фіксованими id згідно з вимогами
                for cat in data.get("categories", []):
                    connection.execute(
                        "INSERT INTO categories (id, name) VALUES (?, ?)",
                        (cat["id"], cat["name"]),
                    )

                # Вставка записів
                for rec in data.get("records", []):
                    connection.execute(
                        """
                        INSERT INTO records (code, title, category_id, value, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            rec["code"],
                            rec["title"],
                            rec["category_id"],
                            rec["value"],
                            rec["status"],
                        ),
                    )
            print("Базу даних успішно заповнено початковими даними!")
        except sqlite3.Error as e:
            connection.rollback()
            print(f"Помилка під час заповнення бази даних: {e}")
            raise


if __name__ == "__main__":
    seed_database()
