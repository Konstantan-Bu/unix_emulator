#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python src/main.py --vfs vfs/files.csv --script scripts/startup/stage5.emu