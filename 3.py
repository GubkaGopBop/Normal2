import argparse
import sys
import json
import urllib.request
import urllib.error
import os


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
    if args.test_mode and not os.path.isfile(args.repo_url):
        errors.append(f"Ошибка: в тестовом режиме файл '{args.repo_url}' не найден")
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


def load_test_repository(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Ошибка: файл '{file_path}' не найден", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка: не удалось разобрать JSON в файле '{file_path}': {e}", file=sys.stderr)
        return None


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
            return None
    if version not in releases:
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


def get_direct_dependencies_pypi(package_name, version, repo_url):
    package_data = get_package_info(package_name, repo_url)
    if not package_data:
        return []
    actual_version = get_version_info(package_data, version)
    if not actual_version:
        return []
    if actual_version == package_data.get('info', {}).get('version'):
        info = package_data.get('info', {})
        requires_dist = info.get('requires_dist', [])
        dependencies = parse_requires_dist(requires_dist)
        return dependencies
    return []


def get_direct_dependencies_test(package_name, test_repo):
    if package_name not in test_repo:
        return []
    return test_repo[package_name]


def build_dependency_graph_dfs(package_name, repo_url, test_mode, test_repo, max_depth, filter_substring, visited,
                               graph, current_depth=0, path=None):
    if path is None:
        path = []
    if max_depth is not None and current_depth >= max_depth:
        return
    if filter_substring and filter_substring in package_name:
        return
    if package_name in path:
        return
    if package_name not in visited:
        visited.add(package_name)
        graph[package_name] = []

    if test_mode:
        dependencies = get_direct_dependencies_test(package_name, test_repo)
    else:
        dependencies = get_direct_dependencies_pypi(package_name, 'latest', repo_url)

    filtered_deps = [dep for dep in dependencies if not (filter_substring and filter_substring in dep)]
    for dep in filtered_deps:
        if dep not in graph[package_name]:
            graph[package_name].append(dep)

    new_path = path + [package_name]
    for dep in filtered_deps:
        build_dependency_graph_dfs(dep, repo_url, test_mode, test_repo, max_depth, filter_substring, visited, graph,
                                   current_depth + 1, new_path)


def print_graph(graph):
    print("\nГраф зависимостей:")
    if not graph:
        print("  (пусто)")
        return
    for package, deps in sorted(graph.items()):
        if deps:
            print(f"  {package} -> {', '.join(deps)}")
        else:
            print(f"  {package} (нет зависимостей)")


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

    test_repo = None
    if args.test_mode:
        print(f"Загрузка тестового репозитория из '{args.repo_url}'...")
        test_repo = load_test_repository(args.repo_url)
        if test_repo is None:
            sys.exit(1)
        print(f"Загружено пакетов: {len(test_repo)}")

    print(f"\nПостроение графа зависимостей для пакета '{args.package}'...")
    visited = set()
    graph = {}
    build_dependency_graph_dfs(args.package, args.repo_url, args.test_mode, test_repo, args.max_depth, args.filter,
                               visited, graph)
    print_graph(graph)
    print(f"\nВсего проанализировано пакетов: {len(graph)}")
    print("\nЭтап 3 завершен успешно")


if __name__ == '__main__':
    main()