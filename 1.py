import argparse
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Визуализация графа зависимостей пакетов Python'
    )

    parser.add_argument('--package', type=str, required=True, help='Имя анализируемого пакета')
    parser.add_argument('--repo-url', type=str, default='https://pypi.org/pypi',
                        help='URL-адрес репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test-mode', action='store_true', help='Режим работы с тестовым репозиторием')
    parser.add_argument('--version', type=str, default='latest', help='Версия пакета')
    parser.add_argument('--output', type=str, default='dependencies.png',
                        help='Имя сгенерированного файла с изображением графа')
    parser.add_argument('--ascii-tree', action='store_true', help='Режим вывода зависимостей в формате ASCII-дерева')
    parser.add_argument('--max-depth', type=int, default=None, help='Максимальная глубина анализа зависимостей')
    parser.add_argument('--filter', type=str, default='', help='Подстрока для фильтрации пакетов')

    return parser.parse_args()


def validate_arguments(args):
    errors = []

    if not args.package or not args.package.strip():
        errors.append("Ошибка: имя пакета не может быть пустым")
    if not args.repo_url or not args.repo_url.strip():
        errors.append("Ошибка: URL репозитория не может быть пустым")
    if not args.version or not args.version.strip():
        errors.append("Ошибка: версия пакета не может быть пустой")
    if not args.output or not args.output.strip():
        errors.append("Ошибка: имя выходного файла не может быть пустым")
    elif not args.output.endswith('.png'):
        errors.append("Ошибка: выходной файл должен иметь расширение .png")
    if args.max_depth is not None and args.max_depth < 0:
        errors.append("Ошибка: максимальная глубина не может быть отрицательной")
    if args.filter is None:
        errors.append("Ошибка: фильтр не может быть None")

    return errors


def print_configuration(args):
    print("=== Конфигурация приложения ===")
    print(f"Имя пакета: {args.package}")
    print(f"URL репозитория: {args.repo_url}")
    print(f"Режим тестового репозитория: {args.test_mode}")
    print(f"Версия пакета: {args.version}")
    print(f"Выходной файл: {args.output}")
    print(f"ASCII-дерево: {args.ascii_tree}")
    print(f"Максимальная глубина: {args.max_depth if args.max_depth is not None else 'не ограничена'}")
    print(f"Фильтр пакетов: '{args.filter}' {'(пусто)' if not args.filter else ''}")
    print("=" * 32)


def main():
    try:
        args = parse_arguments()
    except SystemExit as e:
        if e.code != 0:
            print("\nОшибка: неверные аргументы командной строки", file=sys.stderr)
        sys.exit(e.code)

    errors = validate_arguments(args)
    if errors:
        print("\nОбнаружены ошибки в параметрах:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    print_configuration(args)
    print("\nЭтап 1 завершен успешно")


if __name__ == '__main__':
    main()