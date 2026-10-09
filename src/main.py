# === ИМПОРТЫ ===
# Импорт = подключение готовых инструментов из стандартной библиотеки Python.

import argparse   # разбор аргументов командной строки (--vfs, --script)
import csv        # чтение и разбор CSV-файлов (новое на этапе 3)
import getpass    # получить имя текущего пользователя системы
import os         # работа с ОС: переменные окружения и т.п.
import shlex      # умный разбор строки на слова (учитывает кавычки)
import socket     # работа с сетью, тут — получить имя компьютера
import sys        # доступ к sys.argv — аргументам запуска


# === КОНСТАНТЫ ===
# Константа = переменная, значение которой мы не меняем. Пишут ЗАГЛАВНЫМИ.

DEFAULT_VFS_PATH = None                    # путь к VFS по умолчанию (нет)
DEFAULT_SCRIPT_PATH = None                 # путь к скрипту по умолчанию (нет)
PROMPT_USER_HOST_FMT = "{user}@{host}:~$ " # шаблон приглашения
SCRIPT_COMMENT_PREFIX = "#"                # символ комментария в .emu
EXIT_COMMAND = "exit"                      # имя команды выхода

# Новые константы для VFS:
VFS_DEFAULT_NAME = "default"               # имя VFS по умолчанию
CSV_COLUMNS = ("path", "type", "content")  # обязательные колонки CSV
NODE_TYPE_DIR = "dir"                      # тип узла: папка
NODE_TYPE_FILE = "file"                    # тип узла: файл


# === ФУНКЦИЯ: собрать приглашение ===

def get_prompt():
    """Формирует приглашение вида username@hostname:~$."""
    user = getpass.getuser()                # имя пользователя ОС
    hostname = socket.gethostname()         # имя компьютера
    return PROMPT_USER_HOST_FMT.format(user=user, host=hostname)


# === ФУНКЦИЯ: разобрать аргументы командной строки ===

def parse_args(argv):
    """Разбирает аргументы командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog="unix_emulator",
        description="Эмулятор командной строки UNIX-подобной ОС (Этап 3).",
    )
    # Опция --vfs: путь к CSV-файлу VFS
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default=DEFAULT_VFS_PATH,
        help="Путь к физическому расположению VFS (CSV).",
    )
    # Опция --script: путь к стартовому скрипту
    parser.add_argument(
        "--script",
        dest="script_path",
        default=DEFAULT_SCRIPT_PATH,
        help="Путь к стартовому скрипту с командами эмулятора.",
    )
    return parser.parse_args(argv)


# === ФУНКЦИЯ: напечатать конфигурацию ===

def print_debug_config(args):
    """Отладочный вывод всех заданных параметров при запуске."""
    print("=== Emulator configuration ===")
    print(f"vfs_path    = {args.vfs_path}")
    print(f"script_path = {args.script_path}")
    print("==============================")


# === ФУНКЦИЯ: создать VFS по умолчанию ===
# Возвращает словарь с одним корневым узлом "/" — пустая папка.

def create_default_vfs():
    """Создаёт VFS по умолчанию — только корень / в памяти."""
    return {"/": {NODE_TYPE_DIR: True, "children": {}}}


# === ФУНКЦИЯ: проверить строку CSV ===
# Строка валидна, если в ней есть все нужные колонки и корректный тип.

def _validate_row(row):
    """Проверяет, что строка CSV содержит нужные колонки."""
    if row is None:
        return False
    # Проверяем, что все три колонки вообще есть
    for column in CSV_COLUMNS:
        if column not in row:
            return False
    # Проверяем, что тип — "dir" или "file"
    if row["type"] not in (NODE_TYPE_DIR, NODE_TYPE_FILE):
        return False
    # Проверяем, что путь не пустой
    if not row["path"]:
        return False
    return True


# === ФУНКЦИЯ: вставить узел в дерево VFS ===
# По пути "/home/user/file.txt" создаём нужные вложенные папки
# и кладём файл в правильное место.

def _insert_node(root, path, node_type, content):
    """Вставляет узел в дерево VFS по полному пути."""
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return
    # Начинаем с корневого узла "/", а не с самого словаря root
    current = root["/"]
    for part in parts[:-1]:
        children = current.setdefault("children", {})
        if part not in children:
            children[part] = {NODE_TYPE_DIR: True, "children": {}}
        current = children[part]
    leaf = parts[-1]
    children = current.setdefault("children", {})
    if node_type == NODE_TYPE_DIR:
        children.setdefault(leaf, {NODE_TYPE_DIR: True, "children": {}})
    else:
        children[leaf] = {NODE_TYPE_DIR: False, "content": content}


# === ФУНКЦИЯ: загрузить VFS из CSV ===

def load_vfs(csv_path):
    """Загружает VFS из CSV-файла и возвращает корневой узел."""
    root = create_default_vfs()
    # Открываем файл. newline="" — правильно для csv на Windows.
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)   # читает CSV как словари по колонкам
        for row in reader:
            if not _validate_row(row):
                # Если строка битая — говорим об этом вызывающему коду
                raise ValueError(f"Некорректная строка CSV: {row}")
            _insert_node(
                root,
                row["path"],
                row["type"],
                row.get("content") or None,
            )
    return root


# === ФУНКЦИЯ: посчитать узлы в дереве VFS ===

def _count_nodes(node):
    """Считает количество узлов в дереве VFS (включая корень)."""
    total = 1
    for child in node.get("children", {}).values():
        total += _count_nodes(child)   # рекурсия — функция зовёт саму себя
    return total


# === ФУНКЦИЯ: напечатать информацию о VFS ===

def print_vfs_info(vfs_root, source_name):
    """Печатает краткую информацию о загруженной VFS."""
    total = _count_nodes(vfs_root["/"])
    root_children = vfs_root["/"]["children"]
    # sorted() — чтобы имена шли по алфавиту
    names = ", ".join(sorted(root_children.keys())) or "(пусто)"
    print("=== VFS loaded ===")
    print(f"source: {source_name}")
    print(f"nodes: {total}")
    print(f"root children: {names}")
    print("==================")


# === ФУНКЦИЯ: попытаться загрузить VFS с обработкой ошибок ===

def try_load_vfs(vfs_path):
    """Загружает VFS из файла или создаёт по умолчанию при ошибке."""
    # Если путь не передан — сразу дефолтный
    if not vfs_path:
        print("(VFS path not provided — using default in-memory VFS)")
        root = create_default_vfs()
        print_vfs_info(root, VFS_DEFAULT_NAME)
        return root

    # Пробуем загрузить из файла, ловим типичные ошибки
    try:
        root = load_vfs(vfs_path)
    except FileNotFoundError:
        print(f"shell: VFS file not found: {vfs_path}")
        print("(falling back to default in-memory VFS)")
        root = create_default_vfs()
        print_vfs_info(root, VFS_DEFAULT_NAME)
        return root
    except (ValueError, csv.Error) as error:
        print(f"shell: invalid VFS format: {error}")
        print("(falling back to default in-memory VFS)")
        root = create_default_vfs()
        print_vfs_info(root, VFS_DEFAULT_NAME)
        return root

    print_vfs_info(root, vfs_path)
    return root


# === ФУНКЦИЯ: выполнить одну команду ===
# Пока всё ещё заглушки. Настоящая работа с VFS — на этапе 4.

def execute_command(command, args):
    """Выполняет одну команду эмулятора."""
    if command == EXIT_COMMAND:
        print("Exiting...")
        return False

    if command == "ls":
        print(f"ls: arguments -> {args}")
        return True

    if command == "cd":
        print(f"cd: arguments -> {args}")
        return True

    print(f"shell: command not found: {command}")
    return True


# === ФУНКЦИЯ: разобрать и выполнить строку ===

def run_line(line, prompt, echo):
    """Разбирает и выполняет одну строку ввода."""
    stripped = line.strip()

    if not stripped or stripped.startswith(SCRIPT_COMMENT_PREFIX):
        return True

    expanded = os.path.expandvars(stripped)

    if echo:
        print(f"{prompt}{stripped}")

    try:
        parts = shlex.split(expanded)
    except ValueError as error:
        print(f"shell: {error}")
        return True

    if not parts:
        return True

    command = parts[0]
    args = parts[1:]
    return execute_command(command, args)


# === ФУНКЦИЯ: интерактивный режим ===

def run_interactive():
    """Запускает интерактивный цикл REPL."""
    prompt = get_prompt()
    while True:
        try:
            line = input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            return

        keep_going = run_line(line, prompt, echo=False)
        if not keep_going:
            return


# === ФУНКЦИЯ: выполнить стартовый скрипт ===

def run_startup_script(script_path):
    """Выполняет стартовый скрипт построчно, ошибки пропускает."""
    try:
        with open(script_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"shell: startup script not found: {script_path}")
        return True
    except OSError as error:
        print(f"shell: cannot read startup script: {error}")
        return True

    print(f"--- Executing startup script: {script_path} ---")
    prompt = get_prompt()

    for line in lines:
        keep_going = run_line(line, prompt, echo=True)
        if not keep_going:
            print("--- Startup script finished ---")
            return False

    print("--- Startup script finished ---")
    return True


# === ТОЧКА ВХОДА ===

def main(argv=None):
    """Точка входа приложения."""
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    print_debug_config(args)

    # Загружаем VFS (или дефолтный, если путь не задан / файл битый)
    vfs_root = try_load_vfs(args.vfs_path)

    should_continue = True
    if args.script_path:
        should_continue = run_startup_script(args.script_path)

    if should_continue:
        run_interactive()

    # vfs_root пока не используется командами — пригодится на этапе 4
    _ = vfs_root


# Запускается только если файл вызван напрямую: python src/main.py
if __name__ == "__main__":
    main()