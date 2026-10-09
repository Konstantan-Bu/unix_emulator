#!/bin/bash
set -e
cd "$(dirname "$0")/../.."

echo ">>> Режим: только --script"
python src/main.py --script scripts/startup/basic.emu

echo ">>> Режим: --vfs minimal"
python src/main.py --vfs vfs/minimal.csv --script scripts/startup/basic.emu

echo ">>> Режим: --vfs small"
python src/main.py --vfs vfs/small.csv --script scripts/startup/basic.emu

echo ">>> Режим: --vfs deep"
python src/main.py --vfs vfs/deep.csv --script scripts/startup/vfs_test.emu

echo ">>> Режим: --vfs broken (ошибка + fallback)"
python src/main.py --vfs vfs/broken.csv --script scripts/startup/basic.emu

echo ">>> Режим: без --vfs (default)"
python src/main.py --script scripts/startup/basic.emu

echo ">>> Все режимы выполнены."