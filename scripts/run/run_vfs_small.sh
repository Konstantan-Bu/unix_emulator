#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python src/main.py --vfs vfs/small.csv --script scripts/startup/basic.emu