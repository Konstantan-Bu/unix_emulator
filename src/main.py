# === ИМПОРТЫ ===
# Импорт = подключение готовых инструментов из стандартной библиотеки Python.
# Каждый import даёт нам функции, которые кто-то уже написал за нас.

import argparse   # разбор аргументов командной строки (--vfs, --script)
import getpass    # получить имя текущего пользователя системы
import os         # работа с ОС: переменные окружения и т.п.
import shlex      # умный разбор строки на слова (учитывает кавычки)
import socket     # работа с сетью, тут — получить имя компьютера
import sys        # доступ к sys.argv — аргументам, с которыми запущен скрипт


# === КОНСТАНТЫ ===
# Константы это переменные которые мы не меняем

DEFAULT_VFS_PATH = None         # путь к VFS по умолчанию (пока нет) VFS = игрушечная файловая система
DEFAULT_SCRIPT_PATH = None      # путь к скрипту по умолчанию (пока нет)
PROMPT_USER_HOST_FMT = "{user}@{host}:~$ "   # шаблон приглашения
SCRIPT_COMMENT_PREFIX = "#"     # символ, с которого начинается комментарий в .emu
EXIT_COMMAND = "exit"           # имя команды выхода


# === ФУНКЦИЯ: собрать приглашение ===
# def имя(аргументы): — так объявляется функция.
# Возвращает значение через return.

def get_prompt():
    """Формирует приглашение вида username@hostname:~$."""
    user = getpass.getuser()      # берём имя пользователя ОС
    hostname = socket.gethostname()  # берём имя компьютера
    # .format подставляет значения в шаблон по именам {user} и {host}
    return PROMPT_USER_HOST_FMT.format(user=user, host=hostname)


# === ФУНКЦИЯ: разобрать аргументы командной строки ===
# argv — список строк, например ["--vfs", "vfs/sample.json"]

def parse_args(argv):
    """Разбирает аргументы командной строки эмулятора."""
    # ArgumentParser — объект, который сам умеет читать --help и ловить ошибки
    parser = argparse.ArgumentParser(
        prog="unix_emulator",                                     # имя программы в --help
        description="Эмулятор командной строки UNIX-подобной ОС (Этап 2).",
    )
    # Добавляем опцию --vfs. Если её не передали — значение будет None
    parser.add_argument(
        "--vfs",                       # как писать в командной строке
        dest="vfs_path",               # в какое поле положить значение
        default=DEFAULT_VFS_PATH,      # значение по умолчанию
        help="Путь к физическому расположению VFS.",
    )
    # Добавляем опцию --script
    parser.add_argument(
        "--script",
        dest="script_path",
        default=DEFAULT_SCRIPT_PATH,
        help="Путь к стартовому скрипту с командами эмулятора.",
    )
    # parse_args читает argv и возвращает объект с полями vfs_path и script_path
    return parser.parse_args(argv)


# === ФУНКЦИЯ: напечатать конфигурацию ===
# ничего не делает, просто печатает значения, которые мы получили из командной строки
def print_debug_config(args):
    """Отладочный вывод всех заданных параметров при запуске."""
    # args — это объект от argparse. args.vfs_path и args.script_path — его поля.
    print("=== Emulator configuration ===")
    print(f"vfs_path    = {args.vfs_path}")       # f"..." — подставляет значение в строку
    print(f"script_path = {args.script_path}")
    print("==============================")


# === ФУНКЦИЯ: выполнить одну команду ===
# command — строка ("ls", "cd", ...), args — список слов-аргументов

def execute_command(command, args):
    """Выполняет одну команду эмулятора.
    Возвращает True — работать дальше, False — выйти.
    """
    # Если команда exit — печатаем, что выходим, и говорим "дальше не надо"
    if command == EXIT_COMMAND:
        print("Exiting...")
        return False

    # Заглушка ls: печатает имя команды и её аргументы
    if command == "ls":
        print(f"ls: arguments -> {args}")
        return True

    # Заглушка cd: то же самое
    if command == "cd":
        print(f"cd: arguments -> {args}")
        return True

    # Если ни одна из известных команд не сработала — сообщаем об ошибке
    print(f"shell: command not found: {command}")
    return True   # эмулятор продолжает работу


# === ФУНКЦИЯ: разобрать и выполнить строку ===
# line — что ввёл пользователь, prompt — приглашение, echo — печатать ли ввод

def run_line(line, prompt, echo):
    """Разбирает и выполняет одну строку ввода."""

    # .strip() убирает пробелы и \n в начале и в конце
    stripped = line.strip()

    # Если строка пустая ИЛИ начинается с # — пропускаем её
    if not stripped or stripped.startswith(SCRIPT_COMMENT_PREFIX):
        return True

    # os.path.expandvars заменяет $HOME, $USER и т.п. на реальные значения
    expanded = os.path.expandvars(stripped)

    # Если echo=True (режим скрипта) — печатаем "приглашение + команда",
    # как будто пользователь сам её ввёл
    if echo:
        print(f"{prompt}{stripped}")

    # shlex.split режет строку на слова с учётом кавычек:
    # 'ls "my file"' -> ['ls', 'my file']
    # Если кавычки незакрыты — выбрасывается ValueError
    try:
        parts = shlex.split(expanded)
    except ValueError as error:
        print(f"shell: {error}")
        return True   # пропускаем плохую строку, работаем дальше

    # Если после разбора ничего не осталось — пропускаем
    if not parts:
        return True

    command = parts[0]    # первое слово — команда
    args = parts[1:]      # остальные — аргументы
    # Передаём управление другой функции; она вернёт True/False
    return execute_command(command, args)


# === ФУНКЦИЯ: интерактивный режим ===

def run_interactive():
    """Запускает интерактивный цикл REPL (Read-Eval-Print Loop)."""
    prompt = get_prompt()   # один раз посчитали приглашение
    while True:             # бесконечный цикл — пока не выйдем через return/break
        try:
            # input() печатает prompt и ждёт ввод пользователя
            line = input(prompt)
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C или Ctrl+D — выходим аккуратно
            print("\nExiting...")
            return

        # Выполняем строку. echo=False, потому что пользователь сам её ввёл.
        keep_going = run_line(line, prompt, echo=False)
        # Если была команда exit — run_line вернёт False — выходим
        if not keep_going:
            return


# === ФУНКЦИЯ: выполнить стартовый скрипт ===

def run_startup_script(script_path):
    """Выполняет стартовый скрипт построчно, ошибки пропускает."""

    # Пытаемся открыть файл. Если его нет — FileNotFoundError.
    # encoding="utf-8" — чтобы читались русские буквы.
    try:
        with open(script_path, "r", encoding="utf-8") as file:
            lines = file.readlines()   # читаем все строки в список
    except FileNotFoundError:
        print(f"shell: startup script not found: {script_path}")
        return True   # переходим в REPL
    except OSError as error:
        print(f"shell: cannot read startup script: {error}")
        return True

    print(f"--- Executing startup script: {script_path} ---")
    prompt = get_prompt()

    # Проходим по строкам по очереди
    for line in lines:
        # echo=True — печатаем "приглашение + строка" как имитацию диалога
        keep_going = run_line(line, prompt, echo=True)
        if not keep_going:
            # Встретили exit — прекращаем выполнение скрипта
            print("--- Startup script finished ---")
            return False

    print("--- Startup script finished ---")
    return True   # дошли до конца скрипта без exit — идём в REPL


# === ТОЧКА ВХОДА ===

def main(argv=None):
    """Точка входа приложения."""
    # Если argv не передали — берём аргументы из командной строки
    if argv is None:
        argv = sys.argv[1:]   # [1:] — пропускаем имя файла, берём только опции

    args = parse_args(argv)             # разобрали аргументы
    print_debug_config(args)            # напечатали, что получили

    should_continue = True
    # Если передан --script — выполняем скрипт
    if args.script_path:
        should_continue = run_startup_script(args.script_path)

    # Если после скрипта не было exit — идём в интерактивный режим
    if should_continue:
        run_interactive()


# Эта конструкция означает:
# "если файл запущен напрямую (python main.py), вызови main()".
# Если его импортируют как модуль — main() НЕ вызовется.
if __name__ == "__main__":
    main()