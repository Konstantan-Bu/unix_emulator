import argparse
import getpass
import os
import shlex
import socket
import sys


# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

DEFAULT_VFS_PATH = None
DEFAULT_SCRIPT_PATH = None
PROMPT_USER_HOST_FMT = "{user}@{host}:~$ "
SCRIPT_COMMENT_PREFIX = "#"
EXIT_COMMAND = "exit"


# ---------------------------------------------------------------------------
# Приглашение
# ---------------------------------------------------------------------------

def get_prompt():
    """Формирует приглашение вида username@hostname:~$."""
    user = getpass.getuser()
    hostname = socket.gethostname()
    return PROMPT_USER_HOST_FMT.format(user=user, host=hostname)


# ---------------------------------------------------------------------------
# Парсинг аргументов командной строки
# ---------------------------------------------------------------------------

def parse_args(argv):
    """Разбирает аргументы командной строки эмулятора.

    Args:
        argv: список аргументов (обычно sys.argv[1:]).

    Returns:
        argparse.Namespace с полями vfs_path и script_path.
    """
    parser = argparse.ArgumentParser(
        prog="unix_emulator",
        description="Эмулятор командной строки UNIX-подобной ОС (Этап 2).",
    )
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default=DEFAULT_VFS_PATH,
        help="Путь к физическому расположению VFS.",
    )
    parser.add_argument(
        "--script",
        dest="script_path",
        default=DEFAULT_SCRIPT_PATH,
        help="Путь к стартовому скрипту с командами эмулятора.",
    )
    return parser.parse_args(argv)


def print_debug_config(args):
    """Отладочный вывод всех заданных параметров при запуске."""
    print("=== Emulator configuration ===")
    print(f"vfs_path    = {args.vfs_path}")
    print(f"script_path = {args.script_path}")
    print("==============================")


# ---------------------------------------------------------------------------
# Выполнение одной команды
# ---------------------------------------------------------------------------

def execute_command(command, args):
    """Выполняет одну команду эмулятора.

    Args:
        command: имя команды (str).
        args: список аргументов (list[str]).

    Returns:
        True, если эмулятор должен продолжать работу.
        False, если была выполнена команда выхода (exit).
    """
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


# ---------------------------------------------------------------------------
# Разбор и выполнение строки
# ---------------------------------------------------------------------------

def run_line(line, prompt, echo):
    """Разбирает и выполняет одну строку ввода.

    Args:
        line: строка ввода (str).
        prompt: приглашение для имитации диалога (str).
        echo: если True, печатает приглашение + строку перед выполнением.

    Returns:
        True, если эмулятор должен продолжать работу.
        False, если была выполнена команда выхода.
    """
    stripped = line.strip()

    # Пустые строки и комментарии пропускаем
    if not stripped or stripped.startswith(SCRIPT_COMMENT_PREFIX):
        return True

    # Раскрываем переменные окружения реальной ОС
    expanded = os.path.expandvars(stripped)

    if echo:
        print(f"{prompt}{stripped}")

    # Разбираем с учётом кавычек
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


# ---------------------------------------------------------------------------
# Интерактивный режим (REPL)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Режим стартового скрипта
# ---------------------------------------------------------------------------

def run_startup_script(script_path):
    """Выполняет стартовый скрипт последовательно, пропуская ошибки.

    Args:
        script_path: путь к файлу скрипта (str).

    Returns:
        True, если после скрипта нужно перейти в REPL.
        False, если скрипт завершил работу командой exit.
    """
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


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

def main(argv=None):
    """Точка входа приложения."""
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    print_debug_config(args)

    should_continue = True
    if args.script_path:
        should_continue = run_startup_script(args.script_path)

    if should_continue:
        run_interactive()


if __name__ == "__main__":
    main()