# UNIX Command Line Emulator

Эмулятор командной строки UNIX-подобной ОС. Лабораторный практикум по
конфигурационному управлению, вариант №5.

## Что уже сделано

### Этап 1 — REPL

- Консольный интерфейс с приглашением вида `username@hostname:~$`.
- Парсер умеет раскрывать переменные окружения (`$HOME` и т.п.).
- Заглушки команд `ls` и `cd` — печатают своё имя и аргументы.
- `exit` завершает работу.
- Ошибки (неизвестная команда, незакрытые кавычки) обрабатываются,
  эмулятор не падает.

### Этап 2 — Конфигурация

- Аргументы командной строки:
  - `--vfs PATH` — путь к VFS;
  - `--script PATH` — путь к стартовому скрипту.
- При запуске печатаются все переданные параметры (отладочный вывод).
- Стартовый скрипт читается построчно, команды выполняются по очереди.
- Ошибочная строка не прерывает работу — выводится сообщение и
  выполнение продолжается (требование варианта №5).
- Для каждой строки скрипта печатается приглашение + сама команда, потом
  результат — как будто пользователь вводит вручную.
- Поддерживаются комментарии (`#`) и пустые строки.
- Если файл скрипта не читается — выводится понятное сообщение.
- В `scripts/run/` лежат shell-скрипты для запуска эмулятора во всех
  режимах.

## Структура

    unix_emulator/
    ├── src/
    │   └── main.py            точка входа
    ├── tests/
    ├── scripts/
    │   ├── startup/           скрипты команд для эмулятора (.emu)
    │   └── run/               shell-скрипты для реальной ОС (.sh)
    ├── vfs/                   пример VFS (заглушка под этап 3)
    ├── .gitignore
    └── README.md

## Как запускать

Нужен Python 3.8+.

Интерактивный режим:

    python src/main.py

Со стартовым скриптом:

    python src/main.py --script scripts/startup/basic.emu

С VFS и скриптом:

    python src/main.py --vfs vfs/sample.json --script scripts/startup/basic.emu

Через shell-обёртки (Linux/macOS/Git Bash):

    chmod +x scripts/run/*.sh
    ./scripts/run/run_basic.sh
    ./scripts/run/run_errors.sh
    ./scripts/run/run_vfs.sh
    ./scripts/run/run_all.sh

## Команды

    ls [args]   заглушка, печатает имя и аргументы
    cd [args]   заглушка, печатает имя и аргументы
    exit        завершение работы

## Формат файла .emu

- одна команда на строку;
- пустые строки игнорируются;
- строки, начинающиеся с `#`, — комментарии;
- при ошибке в команде выводится сообщение, выполнение продолжается.

## Пример

Запуск `python src/main.py --script scripts/startup/errors.emu`:

    === Emulator configuration ===
    vfs_path    = None
    script_path = scripts/startup/errors.emu
    ==============================
    --- Executing startup script: scripts/startup/errors.emu ---
    user@host:~$ ls
    ls: arguments -> []
    user@host:~$ badcommand
    shell: command not found: badcommand
    user@host:~$ cd /tmp
    cd: arguments -> ['/tmp']
    user@host:~$ anotherbadcommand
    shell: command not found: anotherbadcommand
    user@host:~$ ls
    ls: arguments -> []
    user@host:~$ exit
    Exiting...
    --- Startup script finished ---

После `badcommand` работа не прерывается — это ключевое отличие
варианта №5 от остальных.

## Тесты

Каталог `tests/` пока пустой — оставлен под автотесты на следующих этапах.

## Этап 3 — VFS (виртуальная файловая система)

- VFS загружается из CSV-файла через аргумент `--vfs`.
- Формат CSV: `path,type,content`, где:
  - `path` — полный путь (`/home/user/file.txt`);
  - `type` — `dir` или `file`;
  - `content` — содержимое (текст или base64, или пусто).
- Вложенность кодируется в пути через `/`.
- Все операции — только в памяти.
- Если `--vfs` не указан — создаётся VFS по умолчанию (только корень `/`).
- Если файл не найден или формат битый — печатается сообщение
  и используется VFS по умолчанию.
- После загрузки выводится отладочная информация:
  источник, количество узлов, список детей корня.

### Пример VFS (CSV)

    path,type,content
    /,dir,
    /home,dir,
    /home/readme.txt,file,SGVsbG8=

### Запуск с VFS

    python src/main.py --vfs vfs/small.csv --script scripts/startup/basic.emu