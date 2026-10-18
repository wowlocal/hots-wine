#!/bin/sh
set -eu
cd "$(dirname "$0")"
clang -target x86_64-pc-windows-msvc -ffreestanding -fno-stack-protector -O2 -c replay-control.c -o replay-control.obj
lld-link /lib /def:user32.def /machine:x64 /out:user32.lib
lld-link /lib /def:kernel32.def /machine:x64 /out:kernel32.lib
lld-link /entry:mainCRTStartup /subsystem:console /nodefaultlib /machine:x64 replay-control.obj user32.lib kernel32.lib /out:replay-control.exe
clang -target x86_64-pc-windows-msvc -ffreestanding -fno-stack-protector -O2 -c dpi-init.c -o dpi-init.obj
lld-link /dll /entry:DllMain /nodefaultlib /machine:x64 dpi-init.obj user32.lib kernel32.lib /out:hots-dpi-init.dll
