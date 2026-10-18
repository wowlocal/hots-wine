#!/bin/sh
set -eu
cd "$(dirname "$0")"
clang -arch x86_64 -dynamiclib -fobjc-arc -fblocks -O2 \
  -framework Foundation -framework QuartzCore -framework Metal \
  frame-probe.m -o frame-probe.dylib
codesign --force --sign - frame-probe.dylib
