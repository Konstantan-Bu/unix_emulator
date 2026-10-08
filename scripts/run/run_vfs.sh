#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python src/main.py --vfs vfs/sample.json --script scripts/startup/basic.emu