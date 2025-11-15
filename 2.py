import argparse
import sys
import json
import urllib.request
import urllib.error


def parse_arguments():
    parser = argparse.ArgumentParser(description='Визуализация графа зависимостей пакетов Python')
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


def get_package_info(package_name, repo_url):
    url = f"{repo_url}/{package_name}/json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        print(f"Ошибка HTTP {e.code}: не удалось получить данные для пакета '{package_name}'", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"Ошибка сети: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: не удалось разобрать JSON для пакета '{package_name}'", file=sys.stderr)
        return None


def get_version_info(package_data, version):
    if not package_data:
        return None
    releases = package_data.get('releases', {})
    if version == 'latest':
        info = package_data.get('info', {})
        version = info.get('version')
        if not version:
            print("Ошибка: не удалось определить последнюю версию", file=sys.stderr)
            return None
    if version not in releases:
        print(f"Ошибка: версия '{version}' не найдена", file=sys.stderr)
        available = list(releases.keys())
        if available:
            print(f"Доступные версии: {', '.join(available[:5])}{'...' if len(available) > 5 else ''}", file=sys.stderr)
        return None
    return version


def parse_requires_dist(requires_dist):
    if not requires_dist:
        return []
    dependencies = []
    for req in requires_dist:
        if ';' in req and 'extra' in req:
            continue
        package_name = \
        req.split()[0].split('(')[0].split('[')[0].split('>')[0].split('<')[0].split('=')[0].split('!')[0].split('~')[0]
        if package_name and package_name not in dependencies:
            dependencies.append(package_name)
    return dependencies


def get_direct_dependencies(package_name, version, repo_url):
    package_data = get_package_info(package_name, repo_url)
    if not package_data:
        return None
    actual_version = get_version_info(package_data, version)
    if not actual_version:
        return None
    releases = package_data.get('releases', {})
    if actual_version == package_data.get('info', {}).get('version'):
        info = package_data.get('info', {})
        requires_dist = info.get('requires_dist', [])
        dependencies = parse_requires_dist(requires_dist)
        return dependencies, actual_version
    return [], actual_version


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
    print()
    print(f"Получение зависимостей для пакета '{args.package}' версии '{args.version}'...")

    result = get_direct_dependencies(args.package, args.version, args.repo_url)
    if result is None:
        print("\nНе удалось получить зависимости", file=sys.stderr)
        sys.exit(1)

    dependencies, actual_version = result
    print(f"\nАнализируется версия: {actual_version}")
    print(f"\nПрямые зависимости пакета '{args.package}':")

    if dependencies:
        for dep in dependencies:
            print(f"  - {dep}")
        print(f"\nВсего зависимостей: {len(dependencies)}")
    else:
        print("  (нет зависимостей)")

    print("\nЭтап 2 завершен успешно")


if __name__ == '__main__':
    main()