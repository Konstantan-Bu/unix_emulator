#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
python src/main.py --vfs vfs/deep.csv --script scripts/startup/vfs_test.emu