#!/bin/bash
set -e
cd "$(dirname "$0")/../.."

echo ">>> Режим 2: только --script"
python src/main.py --script scripts/startup/basic.emu

echo ">>> Режим 3: --vfs + --script"
python src/main.py --vfs vfs/sample.json --script scripts/startup/errors.emu

echo ">>> Режим 4: полный скрипт"
python src/main.py --script scripts/startup/full.emu

echo ">>> Все режимы выполнены."