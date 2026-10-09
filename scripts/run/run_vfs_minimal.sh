#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python src/main.py --vfs vfs/minimal.csv --script scripts/startup/basic.emu