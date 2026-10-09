# === ИМПОРТЫ ===

import argparse   # разбор аргументов командной строки (--vfs, --script)
import base64     # декодирование содержимого файлов из base64
import csv        # чтение и разбор CSV-файлов
import getpass    # получить имя текущего пользователя системы
import os         # работа с ОС: переменные окружения и т.п.
import shlex      # умный разбор строки на слова (учитывает кавычки)
import socket     # работа с сетью, тут — получить имя компьютера
import sys        # доступ к sys.argv — аргументам запуска


# === КОНСТАНТЫ ===

DEFAULT_VFS_PATH = None
DEFAULT_SCRIPT_PATH = None
SCRIPT_COMMENT_PREFIX = "#"
EXIT_COMMAND = "exit"

VFS_DEFAULT_NAME = "default"
CSV_COLUMNS = ("path", "type", "content")
NODE_TYPE_DIR = "dir"
NODE_TYPE_FILE = "file"

ROOT_PATH = "/"
HOME_PATH = "/home"
TAIL_DEFAULT_LINES = 10
UNAME_SHORT = "unix_emulator 1.0"
UNAME_LONG_FMT = (
    "unix_emulator 1.0 (эмуляция UNIX) "
    "host={host} python={py} cwd={cwd}"
)

# Новое на этапе 5:
DEFAULT_OWNER = "user"            # владелец файлов/папок по умолчанию


# === ФУНКЦИЯ: собрать приглашение ===

def get_prompt(cwd):
    """Формирует приглашение вида username@hostname:/path$."""
    user = getpass.getuser()
    hostname = socket.gethostname()
    return f"{user}@{hostname}:{cwd}$ "


# === ФУНКЦИЯ: разобрать аргументы командной строки ===

def parse_args(argv):
    """Разбирает аргументы командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog="unix_emulator",
        description="Эмулятор командной строки UNIX-подобной ОС (Этап 5).",
    )
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default=DEFAULT_VFS_PATH,
        help="Путь к физическому расположению VFS (CSV).",
    )
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

def create_default_vfs():
    """Создаёт VFS по умолчанию — только корень / в памяти."""
    return {"/": {
        NODE_TYPE_DIR: True,
        "children": {},
        "owner": DEFAULT_OWNER,
    }}


# === ФУНКЦИЯ: проверить строку CSV ===

def _validate_row(row):
    """Проверяет, что строка CSV содержит нужные колонки."""
    if row is None:
        return False
    for column in CSV_COLUMNS:
        if column not in row:
            return False
    if row["type"] not in (NODE_TYPE_DIR, NODE_TYPE_FILE):
        return False
    if not row["path"]:
        return False
    return True


# === ФУНКЦИЯ: вставить узел в дерево VFS ===

def _insert_node(root, path, node_type, content):
    """Вставляет узел в дерево VFS по полному пути."""
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return
    current = root["/"]
    for part in parts[:-1]:
        children = current.setdefault("children", {})
        if part not in children:
            children[part] = {
                NODE_TYPE_DIR: True,
                "children": {},
                "owner": DEFAULT_OWNER,
            }
        current = children[part]
    leaf = parts[-1]
    children = current.setdefault("children", {})
    if node_type == NODE_TYPE_DIR:
        if leaf not in children:
            children[leaf] = {
                NODE_TYPE_DIR: True,
                "children": {},
                "owner": DEFAULT_OWNER,
            }
    else:
        children[leaf] = {
            NODE_TYPE_DIR: False,
            "content": content,
            "owner": DEFAULT_OWNER,
        }


# === ФУНКЦИЯ: загрузить VFS из CSV ===

def load_vfs(csv_path):
    """Загружает VFS из CSV-файла и возвращает корневой узел."""
    root = create_default_vfs()
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if not _validate_row(row):
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
        total += _count_nodes(child)
    return total


# === ФУНКЦИЯ: напечатать информацию о VFS ===

def print_vfs_info(vfs_root, source_name):
    """Печатает краткую информацию о загруженной VFS."""
    total = _count_nodes(vfs_root["/"])
    root_children = vfs_root["/"]["children"]
    names = ", ".join(sorted(root_children.keys())) or "(пусто)"
    print("=== VFS loaded ===")
    print(f"source: {source_name}")
    print(f"nodes: {total}")
    print(f"root children: {names}")
    print("==================")


# === ФУНКЦИЯ: попытаться загрузить VFS с обработкой ошибок ===

def try_load_vfs(vfs_path):
    """Загружает VFS из файла или создаёт по умолчанию при ошибке."""
    if not vfs_path:
        print("(VFS path not provided — using default in-memory VFS)")
        root = create_default_vfs()
        print_vfs_info(root, VFS_DEFAULT_NAME)
        return root

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


# === СОСТОЯНИЕ ЭМУЛЯТОРА ===

def create_state(vfs_root):
    """Создаёт начальное состояние эмулятора."""
    return {"vfs": vfs_root, "cwd": ROOT_PATH}


# === ФУНКЦИЯ: нормализовать путь ===

def resolve_path(cwd, target):
    """Возвращает абсолютный путь с учётом cwd."""
    if not target:
        return cwd

    if target == "~":
        return HOME_PATH

    if target.startswith(ROOT_PATH):
        stack = []
    else:
        stack = [p for p in cwd.split("/") if p]

    for part in target.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)

    return ROOT_PATH + "/".join(stack)


# === ФУНКЦИЯ: найти узел по абсолютному пути ===

def get_node(vfs_root, abs_path):
    """Возвращает узел VFS по абсолютному пути или None."""
    if abs_path == ROOT_PATH:
        return vfs_root["/"]
    current = vfs_root["/"]
    for part in abs_path.strip("/").split("/"):
        children = current.get("children", {})
        if part not in children:
            return None
        current = children[part]
    return current


# === ФУНКЦИЯ: разделить путь на родителя и имя ===
# "/home/user/a.txt" → ("/home/user", "a.txt")
# "/a.txt"           → ("/", "a.txt")

def split_parent(abs_path):
    """Возвращает (родительский путь, имя) для абсолютного пути."""
    if abs_path == ROOT_PATH:
        return ROOT_PATH, ""
    parts = [p for p in abs_path.strip("/").split("/") if p]
    if not parts:
        return ROOT_PATH, ""
    parent = ROOT_PATH + "/".join(parts[:-1])
    if parent == "":
        parent = ROOT_PATH
    return parent, parts[-1]


# === ФУНКЦИЯ: декодировать содержимое файла ===

def decode_content(node):
    """Декодирует содержимое файла из base64 в текст."""
    raw = node.get("content")
    if not raw:
        return ""
    try:
        return base64.b64decode(raw).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return ""


# === КОМАНДА: ls ===
# Поддерживает флаг -l / -la — тогда печатает владельца.

def cmd_ls(args, state):
    """Показывает содержимое папки."""
    long_format = False
    rest = list(args)

    if rest and rest[0] in ("-l", "-la", "-al"):
        long_format = True
        rest = rest[1:]

    target = rest[0] if rest else state["cwd"]
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)

    if node is None:
        print(f"ls: cannot access '{target}': No such file or directory")
        return True

    if not node.get(NODE_TYPE_DIR):
        print(f"ls: {target}: Not a directory")
        return True

    children = node.get("children", {})
    if not children:
        return True

    for name in sorted(children.keys()):
        child = children[name]
        suffix = "/" if child.get(NODE_TYPE_DIR) else ""
        if long_format:
            owner = child.get("owner", DEFAULT_OWNER)
            print(f"{owner}  {name}{suffix}")
        else:
            print(f"{name}{suffix}")
    return True


# === КОМАНДА: cd ===

def cmd_cd(args, state):
    """Меняет текущую папку."""
    target = args[0] if args else ROOT_PATH
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)

    if node is None:
        print(f"cd: {target}: No such file or directory")
        return True

    if not node.get(NODE_TYPE_DIR):
        print(f"cd: {target}: Not a directory")
        return True

    state["cwd"] = abs_path
    return True


# === КОМАНДА: tac ===

def cmd_tac(args, state):
    """Выводит файл в обратном порядке строк."""
    if not args:
        print("tac: missing file operand")
        return True
    if len(args) > 1:
        print(f"tac: extra operand '{args[1]}'")
        return True

    target = args[0]
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)

    if node is None:
        print(f"tac: {target}: No such file or directory")
        return True
    if node.get(NODE_TYPE_DIR):
        print(f"tac: {target}: Is a directory")
        return True

    content = decode_content(node)
    for line in reversed(content.splitlines()):
        print(line)
    return True


# === КОМАНДА: tail ===

def cmd_tail(args, state):
    """Выводит последние N строк файла."""
    if not args:
        print("tail: missing file operand")
        return True

    lines_count = TAIL_DEFAULT_LINES
    if args[0] == "-n":
        if len(args) < 2:
            print("tail: option requires an argument -- 'n'")
            return True
        try:
            lines_count = int(args[1])
        except ValueError:
            print(f"tail: invalid number of lines: {args[1]}")
            return True
        if lines_count < 0:
            print(f"tail: invalid number of lines: {lines_count}")
            return True
        rest = args[2:]
    else:
        rest = args

    if not rest:
        print("tail: missing file operand")
        return True
    if len(rest) > 1:
        print(f"tail: extra operand '{rest[1]}'")
        return True

    target = rest[0]
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)

    if node is None:
        print(f"tail: {target}: No such file or directory")
        return True
    if node.get(NODE_TYPE_DIR):
        print(f"tail: {target}: Is a directory")
        return True

    content = decode_content(node)
    lines = content.splitlines()
    for line in lines[-lines_count:]:
        print(line)
    return True


# === КОМАНДА: uname ===

def cmd_uname(args, state):
    """Выводит информацию о системе эмулятора."""
    if args and args[0] == "-a":
        print(UNAME_LONG_FMT.format(
            host=socket.gethostname(),
            py=sys.version.split()[0],
            cwd=state["cwd"],
        ))
        return True

    if args:
        print(f"uname: invalid option: {args[0]}")
        return True

    print(UNAME_SHORT)
    return True


# === КОМАНДА: touch ===
# Создаёт пустой файл в VFS (в памяти). Файл на диске не меняется.

def cmd_touch(args, state):
    """Создаёт пустой файл (или несколько)."""
    if not args:
        print("touch: missing file operand")
        return True

    for target in args:
        abs_path = resolve_path(state["cwd"], target)
        parent_path, name = split_parent(abs_path)

        if not name:
            print(f"touch: cannot touch '{target}': Invalid path")
            continue

        parent = get_node(state["vfs"], parent_path)
        if parent is None or not parent.get(NODE_TYPE_DIR):
            print(
                f"touch: cannot touch '{target}': "
                "No such file or directory"
            )
            continue

        children = parent.setdefault("children", {})
        if name in children:
            existing = children[name]
            if existing.get(NODE_TYPE_DIR):
                print(f"touch: cannot touch '{target}': Is a directory")
            # Если файл уже есть — в реальном touch обновляется mtime.
            # У нас — просто ничего не делаем.
            continue

        children[name] = {
            NODE_TYPE_DIR: False,
            "content": None,
            "owner": DEFAULT_OWNER,
        }
    return True


# === КОМАНДА: chown ===
# Меняет владельца файла или папки в VFS (в памяти).

def cmd_chown(args, state):
    """Меняет владельца файла/папки."""
    if len(args) < 2:
        print("chown: missing operand")
        return True

    owner = args[0]
    targets = args[1:]

    for target in targets:
        abs_path = resolve_path(state["cwd"], target)
        node = get_node(state["vfs"], abs_path)
        if node is None:
            print(
                f"chown: cannot access '{target}': "
                "No such file or directory"
            )
            continue
        node["owner"] = owner
    return True


# === ТАБЛИЦА КОМАНД ===

COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "tac": cmd_tac,
    "tail": cmd_tail,
    "uname": cmd_uname,
    "touch": cmd_touch,
    "chown": cmd_chown,
}


# === ФУНКЦИЯ: выполнить одну команду ===

def execute_command(command, args, state):
    """Выполняет одну команду эмулятора."""
    if command == EXIT_COMMAND:
        print("Exiting...")
        return False

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"shell: command not found: {command}")
        return True

    return handler(args, state)


# === ФУНКЦИЯ: разобрать и выполнить строку ===

def run_line(line, state, echo):
    """Разбирает и выполняет одну строку ввода."""
    stripped = line.strip()

    if not stripped or stripped.startswith(SCRIPT_COMMENT_PREFIX):
        return True

    expanded = os.path.expandvars(stripped)
    prompt = get_prompt(state["cwd"])

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
    return execute_command(command, args, state)


# === ФУНКЦИЯ: интерактивный режим ===

def run_interactive(state):
    """Запускает интерактивный цикл REPL."""
    while True:
        prompt = get_prompt(state["cwd"])
        try:
            line = input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            return

        keep_going = run_line(line, state, echo=False)
        if not keep_going:
            return


# === ФУНКЦИЯ: выполнить стартовый скрипт ===

def run_startup_script(script_path, state):
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
    for line in lines:
        keep_going = run_line(line, state, echo=True)
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

    vfs_root = try_load_vfs(args.vfs_path)
    state = create_state(vfs_root)

    should_continue = True
    if args.script_path:
        should_continue = run_startup_script(args.script_path, state)

    if should_continue:
        run_interactive(state)


# Запускается только если файл вызван напрямую: python src/main.py
if __name__ == "__main__":
    main()