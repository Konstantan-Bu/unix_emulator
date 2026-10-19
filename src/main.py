"""Эмулятор командной строки UNIX-подобной ОС.

Лабораторный практикум по конфигурационному управлению.
Вариант №5.
"""

import argparse
import base64
import csv
import getpass
import os
import shlex
import socket
import sys


DEFAULT_VFS_PATH = None
DEFAULT_SCRIPT_PATH = None
SCRIPT_COMMENT_PREFIX = "#"
EXIT_COMMAND = "exit"

VFS_DEFAULT_NAME = "default"
CSV_COLUMNS = ("path", "type", "content")
NODE_TYPE_DIR = "dir"
NODE_TYPE_FILE = "file"
NODE_CHILDREN = "children"
NODE_OWNER = "owner"
NODE_CONTENT = "content"
DEFAULT_OWNER = "user"

ROOT_PATH = "/"
HOME_PATH = "/home"
TAIL_DEFAULT_LINES = 10
UNAME_SHORT = "unix_emulator 1.0"
UNAME_LONG_FMT = (
    "unix_emulator 1.0 (эмуляция UNIX) "
    "host={host} python={py} cwd={cwd}"
)

LS_LONG_FLAGS = ("-l", "-la", "-al")
ARG_FIRST = 0
ARG_SECOND = 1
MIN_ARGS_CHOWN = 2
MIN_ARGS_TAIL_N = 2
MIN_LINES_COUNT = 0
MAX_EXTRA_ARG = 1


def get_prompt(cwd):
    """Формирует приглашение вида username@hostname:/path$."""
    user = getpass.getuser()
    hostname = socket.gethostname()
    return f"{user}@{hostname}:{cwd}$ "


def _add_vfs_argument(parser):
    """Добавляет аргумент --vfs в парсер."""
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default=DEFAULT_VFS_PATH,
        help="Путь к физическому расположению VFS (CSV).",
    )


def _add_script_argument(parser):
    """Добавляет аргумент --script в парсер."""
    parser.add_argument(
        "--script",
        dest="script_path",
        default=DEFAULT_SCRIPT_PATH,
        help="Путь к стартовому скрипту с командами эмулятора.",
    )


def parse_args(argv):
    """Разбирает аргументы командной строки эмулятора."""
    parser = argparse.ArgumentParser(
        prog="unix_emulator",
        description="Эмулятор командной строки UNIX-подобной ОС.",
    )
    _add_vfs_argument(parser)
    _add_script_argument(parser)
    return parser.parse_args(argv)


def print_debug_config(args):
    """Отладочный вывод всех заданных параметров при запуске."""
    print("=== Emulator configuration ===")
    print(f"vfs_path    = {args.vfs_path}")
    print(f"script_path = {args.script_path}")
    print("==============================")


def _new_dir_node():
    """Создаёт узел-папку."""
    return {
        NODE_TYPE_DIR: True,
        NODE_CHILDREN: {},
        NODE_OWNER: DEFAULT_OWNER,
    }


def _new_file_node(content):
    """Создаёт узел-файл."""
    return {
        NODE_TYPE_DIR: False,
        NODE_CONTENT: content,
        NODE_OWNER: DEFAULT_OWNER,
    }


def create_default_vfs():
    """Создаёт VFS по умолчанию — только корень / в памяти."""
    return {"/": _new_dir_node()}


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


def _get_or_create_dir(parent, name):
    """Возвращает подпапку с именем name; создаёт, если её нет."""
    children = parent.setdefault(NODE_CHILDREN, {})
    if name not in children:
        children[name] = _new_dir_node()
    return children[name]


def _insert_node(root, path, node_type, content):
    """Вставляет узел в дерево VFS по полному пути."""
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return
    current = root["/"]
    for part in parts[:-1]:
        current = _get_or_create_dir(current, part)
    leaf = parts[-1]
    children = current.setdefault(NODE_CHILDREN, {})
    if node_type == NODE_TYPE_DIR:
        if leaf not in children:
            children[leaf] = _new_dir_node()
    else:
        children[leaf] = _new_file_node(content)


def load_vfs(csv_path):
    """Загружает VFS из CSV-файла и возвращает корневой узел."""
    root = create_default_vfs()
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if not _validate_row(row):
                raise ValueError(f"Некорректная строка CSV: {row}")
            content = row.get("content") or None
            _insert_node(root, row["path"], row["type"], content)
    return root


def _count_nodes(node):
    """Считает количество узлов в дереве VFS (включая корень)."""
    total = 1
    for child in node.get(NODE_CHILDREN, {}).values():
        total += _count_nodes(child)
    return total


def print_vfs_info(vfs_root, source_name):
    """Печатает краткую информацию о загруженной VFS."""
    total = _count_nodes(vfs_root["/"])
    root_children = vfs_root["/"][NODE_CHILDREN]
    names = ", ".join(sorted(root_children.keys())) or "(пусто)"
    print("=== VFS loaded ===")
    print(f"source: {source_name}")
    print(f"nodes: {total}")
    print(f"root children: {names}")
    print("==================")


def _fallback_to_default(reason):
    """Возвращает VFS по умолчанию с сообщением о причине."""
    print(reason)
    print("(falling back to default in-memory VFS)")
    root = create_default_vfs()
    print_vfs_info(root, VFS_DEFAULT_NAME)
    return root


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
        msg = f"shell: VFS file not found: {vfs_path}"
        return _fallback_to_default(msg)
    except (ValueError, csv.Error) as error:
        msg = f"shell: invalid VFS format: {error}"
        return _fallback_to_default(msg)

    print_vfs_info(root, vfs_path)
    return root


def create_state(vfs_root):
    """Создаёт начальное состояние эмулятора."""
    return {"vfs": vfs_root, "cwd": ROOT_PATH}


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


def get_node(vfs_root, abs_path):
    """Возвращает узел VFS по абсолютному пути или None."""
    if abs_path == ROOT_PATH:
        return vfs_root["/"]
    current = vfs_root["/"]
    for part in abs_path.strip("/").split("/"):
        children = current.get(NODE_CHILDREN, {})
        if part not in children:
            return None
        current = children[part]
    return current


def split_parent(abs_path):
    """Возвращает (родительский путь, имя) для абсолютного пути."""
    if abs_path == ROOT_PATH:
        return ROOT_PATH, ""
    parts = [p for p in abs_path.strip("/").split("/") if p]
    if not parts:
        return ROOT_PATH, ""
    parent = ROOT_PATH + "/".join(parts[:-1])
    if not parent:
        parent = ROOT_PATH
    return parent, parts[-1]


def decode_content(node):
    """Декодирует содержимое файла из base64 в текст."""
    raw = node.get(NODE_CONTENT)
    if not raw:
        return ""
    try:
        return base64.b64decode(raw).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return ""


def _print_dir_entry(name, child, long_format):
    """Печатает одну запись каталога."""
    suffix = "/" if child.get(NODE_TYPE_DIR) else ""
    if long_format:
        owner = child.get(NODE_OWNER, DEFAULT_OWNER)
        print(f"{owner}  {name}{suffix}")
    else:
        print(f"{name}{suffix}")


def _split_ls_args(args):
    """Разбирает флаг -l у ls. Возвращает (long_format, остаток)."""
    if args and args[ARG_FIRST] in LS_LONG_FLAGS:
        return True, list(args[1:])
    return False, list(args)


def cmd_ls(args, state):
    """Показывает содержимое папки."""
    long_format, rest = _split_ls_args(args)
    target = rest[ARG_FIRST] if rest else state["cwd"]
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)

    if node is None:
        print(f"ls: cannot access '{target}': No such file or directory")
        return True
    if not node.get(NODE_TYPE_DIR):
        print(f"ls: {target}: Not a directory")
        return True

    children = node.get(NODE_CHILDREN, {})
    for name in sorted(children.keys()):
        _print_dir_entry(name, children[name], long_format)
    return True


def cmd_cd(args, state):
    """Меняет текущую папку."""
    target = args[ARG_FIRST] if args else ROOT_PATH
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


def _read_file(target, state, command_name):
    """Читает файл VFS. Возвращает текст или None при ошибке."""
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)
    if node is None:
        print(f"{command_name}: {target}: No such file or directory")
        return None
    if node.get(NODE_TYPE_DIR):
        print(f"{command_name}: {target}: Is a directory")
        return None
    return decode_content(node)


def cmd_tac(args, state):
    """Выводит файл в обратном порядке строк."""
    if not args:
        print("tac: missing file operand")
        return True
    if len(args) > MAX_EXTRA_ARG:
        print(f"tac: extra operand '{args[ARG_SECOND]}'")
        return True

    content = _read_file(args[ARG_FIRST], state, "tac")
    if content is None:
        return True
    for line in reversed(content.splitlines()):
        print(line)
    return True


def _parse_tail_count(args):
    """Разбирает флаг -n. Возвращает (count, rest, error)."""
    if args[ARG_FIRST] != "-n":
        return TAIL_DEFAULT_LINES, args, None
    if len(args) < MIN_ARGS_TAIL_N:
        return None, None, "tail: option requires an argument -- 'n'"
    try:
        count = int(args[ARG_SECOND])
    except ValueError:
        value = args[ARG_SECOND]
        return None, None, f"tail: invalid number of lines: {value}"
    if count < MIN_LINES_COUNT:
        return None, None, f"tail: invalid number of lines: {count}"
    return count, args[MIN_ARGS_TAIL_N:], None


def cmd_tail(args, state):
    """Выводит последние N строк файла."""
    if not args:
        print("tail: missing file operand")
        return True

    count, rest, error = _parse_tail_count(args)
    if error:
        print(error)
        return True
    if not rest:
        print("tail: missing file operand")
        return True
    if len(rest) > MAX_EXTRA_ARG:
        print(f"tail: extra operand '{rest[ARG_SECOND]}'")
        return True

    content = _read_file(rest[ARG_FIRST], state, "tail")
    if content is None:
        return True
    for line in content.splitlines()[-count:]:
        print(line)
    return True


def cmd_uname(args, state):
    """Выводит информацию о системе эмулятора."""
    if args and args[ARG_FIRST] == "-a":
        print(UNAME_LONG_FMT.format(
            host=socket.gethostname(),
            py=sys.version.split()[ARG_FIRST],
            cwd=state["cwd"],
        ))
        return True
    if args:
        print(f"uname: invalid option: {args[ARG_FIRST]}")
        return True
    print(UNAME_SHORT)
    return True


def _touch_one(target, state):
    """Создаёт один пустой файл в VFS."""
    abs_path = resolve_path(state["cwd"], target)
    parent_path, name = split_parent(abs_path)
    if not name:
        print(f"touch: cannot touch '{target}': Invalid path")
        return
    parent = get_node(state["vfs"], parent_path)
    if parent is None or not parent.get(NODE_TYPE_DIR):
        print(f"touch: cannot touch '{target}': No such file or directory")
        return
    children = parent.setdefault(NODE_CHILDREN, {})
    if name in children:
        if children[name].get(NODE_TYPE_DIR):
            print(f"touch: cannot touch '{target}': Is a directory")
        return
    children[name] = _new_file_node(None)


def cmd_touch(args, state):
    """Создаёт пустой файл (или несколько)."""
    if not args:
        print("touch: missing file operand")
        return True
    for target in args:
        _touch_one(target, state)
    return True


def _chown_one(owner, target, state):
    """Меняет владельца одного узла."""
    abs_path = resolve_path(state["cwd"], target)
    node = get_node(state["vfs"], abs_path)
    if node is None:
        print(f"chown: cannot access '{target}': No such file or directory")
        return
    node[NODE_OWNER] = owner


def cmd_chown(args, state):
    """Меняет владельца файла/папки."""
    if len(args) < MIN_ARGS_CHOWN:
        print("chown: missing operand")
        return True
    owner = args[ARG_FIRST]
    for target in args[ARG_SECOND:]:
        _chown_one(owner, target, state)
    return True


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "tac": cmd_tac,
    "tail": cmd_tail,
    "uname": cmd_uname,
    "touch": cmd_touch,
    "chown": cmd_chown,
}


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
    return execute_command(parts[0], parts[1:], state)


def run_interactive(state):
    """Запускает интерактивный цикл REPL."""
    while True:
        prompt = get_prompt(state["cwd"])
        try:
            line = input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            return
        if not run_line(line, state, echo=False):
            return


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
        if not run_line(line, state, echo=True):
            print("--- Startup script finished ---")
            return False
    print("--- Startup script finished ---")
    return True


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


if __name__ == "__main__":
    main()