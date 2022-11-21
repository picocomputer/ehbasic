# build basic.c
cc conv.c -o conv
64tass --mw65c02 min_mon.asm
./conv
