# UNIX Command Line Emulator

Эмулятор командной строки UNIX-подобной ОС. Лабораторный практикум по
конфигурационному управлению. **Вариант №5**.

## Описание

Программа представляет собой консольный эмулятор оболочки, работающий с
виртуальной файловой системой (VFS). Поддерживается два режима:
интерактивный (REPL) и выполнение стартового скрипта.

## Структура проекта

    unix_emulator/
    ├── src/
    │   └── main.py            # исходный код
    ├── tests/                 # каталог для автотестов
    ├── scripts/
    │   ├── startup/           # скрипты команд для эмулятора (.emu)
    │   └── run/               # shell-скрипты для реальной ОС (.sh)
    ├── vfs/                   # примеры VFS в формате CSV
    ├── .gitignore
    ├── run.sh                 # скрипт запуска для Linux/macOS/Git Bash
    ├── run.bat                # скрипт запуска для Windows
    └── README.md

## Функциональность по этапам

**Этап 1. REPL**
- Консольный интерфейс (CLI) с приглашением вида `user@host:/path$`.
- Поддержка раскрытия переменных окружения (`$HOME`).
- Обработка ошибок ввода (незакрытые кавычки, неизвестные команды).
- Команда `exit` для корректного выхода.

**Этап 2. Конфигурация**
- Аргументы командной строки: `--vfs PATH` (путь к файлу VFS) и `--script PATH` (путь к скрипту).
- Отладочный вывод параметров при старте.
- Стартовый скрипт выполняется построчно. При ошибке в команде выводится сообщение, а выполнение продолжается (особенность варианта №5).
- Визуализация диалога: для каждой строки скрипта печатается приглашение, сама команда и результат.

**Этап 3. Виртуальная файловая система (VFS)**
- VFS загружается из CSV-файла (`path,type,content`).
- Все операции происходят только в памяти, исходный файл не изменяется.
- Если файл не найден или формат битый — создается VFS по умолчанию (только корень `/`).
- Вложенность файлов и папок кодируется в поле `path` через `/`.

**Этап 4. Основные команды**
- `ls [path]` — вывод содержимого папки (поддерживает флаг `-l` для показа владельца).
- `cd [path]` — смена текущей директории (поддерживает `.`, `..`, `~`).
- `tac <file>` — вывод файла в обратном порядке строк.
- `tail [-n N] <file>` — вывод последних N строк (по умолчанию 10).
- `uname [-a]` — вывод информации о системе.

**Этап 5. Команды, меняющие VFS**
- `touch <file>` — создание пустого файла в памяти.
- `chown <owner> <path>` — смена владельца файла или папки.
- Все изменения существуют только до выхода из эмулятора.

## Как запускать

Нужен Python 3.8+.

**Через скрипты запуска (рекомендуется):**
В Windows:
    run.bat --vfs vfs/files.csv --script scripts/startup/stage5.emu

В Linux/macOS/Git Bash:
    ./run.sh --vfs vfs/files.csv --script scripts/startup/stage5.emu

**Напрямую через Python:**
    python src/main.py --vfs vfs/files.csv --script scripts/startup/stage5.emu

**Интерактивный режим (без скрипта):**
    python src/main.py --vfs vfs/files.csv

## Пример работы

Запуск со скриптом `scripts/startup/stage5.emu`:

    === Emulator configuration ===
    vfs_path    = vfs/files.csv
    script_path = scripts/startup/stage5.emu
    ==============================
    === VFS loaded ===
    source: vfs/files.csv
    nodes: 9
    root children: etc, home
    ==================
    --- Executing startup script: scripts/startup/stage5.emu ---
    User@DESKTOP:/$ cd /home/user
    User@DESKTOP:/home/user$ ls
    docs/
    notes.txt
    todo.txt
    User@DESKTOP:/home/user$ touch newfile.txt
    User@DESKTOP:/home/user$ ls -l
    user  docs/
    user  newfile.txt
    user  notes.txt
    user  todo.txt
    User@DESKTOP:/home/user$ chown root newfile.txt
    User@DESKTOP:/home/user$ ls -l
    user  docs/
    root  newfile.txt
    ...