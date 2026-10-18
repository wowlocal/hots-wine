#!/bin/zsh
set -eu
script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec /usr/bin/env python3 "$script_dir/scripts/play-game.py" dxmt-metal120
