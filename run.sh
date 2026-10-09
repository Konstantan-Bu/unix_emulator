#!/bin/bash
# Универсальный запуск эмулятора.
# Использование: ./run.sh [аргументы эмулятора]
set -e
cd "$(dirname "$0")"
python src/main.py "$@"