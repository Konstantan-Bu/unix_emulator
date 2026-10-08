import os
import sys
import socket
import getpass
import shlex


def get_prompt():
    """Формирует приглашение в формате username@hostname:~$."""
    user = getpass.getuser()
    hostname = socket.gethostname()
    return f"{user}@{hostname}:~$ "


def main():
    """Основной цикл REPL."""
    while True:
        try:
            # Выводим приглашение и читаем команду пользователя
            prompt = get_prompt()
            line = input(prompt).strip()

            # Пустой ввод игнорируем
            if not line:
                continue

            # Раскрываем переменные окружения реальной ОС
            # Например: $HOME -> /home/username
            line = os.path.expandvars(line)

            # Разбираем команду и аргументы с учетом кавычек
            try:
                parts = shlex.split(line)
            except ValueError as error:
                # Обрабатываем ошибки синтаксиса, например незакрытые кавычки
                print(f"shell: {error}")
                continue

            command = parts[0]
            args = parts[1:]

            # Команда выхода
            if command == "exit":
                print("Exiting...")
                break

            # Заглушка команды ls
            elif command == "ls":
                print(f"ls: arguments -> {args}")

            # Заглушка команды cd
            elif command == "cd":
                print(f"cd: arguments -> {args}")

            # Неизвестная команда
            else:
                print(f"shell: command not found: {command}")

        except (KeyboardInterrupt, EOFError):
            # Корректное завершение по Ctrl+C или Ctrl+D
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()