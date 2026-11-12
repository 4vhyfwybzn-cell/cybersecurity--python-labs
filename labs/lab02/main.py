import argparse
from pathlib import Path

from labs.lab02.task1 import Admin, User, UserAccount
from labs.lab02.task2 import ServiceAvailabilityScanner


def run_demo() -> None:
    print("=== ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1 (ООП) ===")

    user = User("developer1", "dev1@company.ua", role="user")
    user.set_password("SecurePass123")
    print(f"Створено користувача: {user}")

    try:
        user.email = "bad-email-format"
    except ValueError as e:
        print(f"[Перехоплено помилку email валідації]: {e}")

    admin = Admin(
        "root_admin", "admin@company.ua", permissions={"READ", "WRITE", "EXECUTE"}
    )
    print(f"Створено адміністратора: {admin}")
    admin.grant_permission("DELETE")
    print(f"Права адміністратора після розширення: {admin.permissions}")

    account = UserAccount(user=user)

    success_fail = account.login("WrongPassword", "192.168.1.50")
    print(f"Спроба входу з невірним паролем: {success_fail}")

    success_ok = account.login("SecurePass123", "192.168.1.50")
    print(f"Спроба входу з вірним паролем: {success_ok}")
    print(f"Чи аутентифікований користувач: {account.is_authenticated()}")

    print(
        f"Доступ до об'єкта через індексатор account['user']: {account['user'].username}"
    )

    account.logout()
    print(f"Після виходу аутентифікований: {account.is_authenticated()}")

    print("\n--- Записи журналу аудиту (AuditLog) ---")
    for record in account["audit_log"].show_all():
        print(
            f"Час: {record.timestamp} | Користувач: {record.username} | Дія: {record.action}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Лабораторна робота №2: Консольні утиліти безпеки (Варіант 5)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "demo", help="Запустити демонстрацію ООП компонентів (Завдання 1)"
    )

    parser_analyze = subparsers.add_parser(
        "analyze", help="Запустити сканер доступності сервісів (Завдання 2)"
    )
    parser_analyze.add_argument(
        "--targets",
        type=str,
        default="labs/lab02/data/data_v05/targets.json",
        help="Шлях до JSON/CSV файлу цілей",
    )
    parser_analyze.add_argument(
        "--timeout", type=float, default=2.0, help="Таймаут з'єднання в секундах"
    )
    parser_analyze.add_argument(
        "--out-csv",
        type=str,
        default="labs/lab02/data/scan_results.csv",
        help="Шлях для збереження результатів у CSV",
    )
    parser_analyze.add_argument(
        "--verbose", action="store_true", help="Детальний режим логування"
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        scanner = ServiceAvailabilityScanner(
            targets_path=Path(args.targets), timeout=args.timeout, verbose=args.verbose
        )
        scanner.scan(out_csv_path=Path(args.out_csv))


if __name__ == "__main__":
    main()
