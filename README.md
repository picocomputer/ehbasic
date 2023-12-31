# RP6502 - Enhanced 6502 BASIC

Reference manual and more information archived here:<br>
http://retro.hansotten.nl/6502-sbc/lee-davison-web-site/enhanced-6502-basic/

You must have on your development system:
 * [VSCode](https://code.visualstudio.com/). This has its own installer.
 * A source install of [this CC65](https://github.com/picocomputer/cc65).
 * The following suite of tools for your specific OS.
```
$ sudo apt-get install cmake python3 pip git build-essential
$ pip install pyserial
```

# Initial plotting enhancements for the RP6502 Picocomputer's EhBASIC
Enhancements work with (were originally targetted to) the 20-Dec-2023 EhBASIC in the master
picocomputer repo (rev: 63ca0e6).

Four new commands are available using EhBasic's "CALL" keyword. 
CALL addresses supplied are from the mapfile. 
Plotting command is callable from EhBASIC.

The commands are:

    * HGR - initializes the 320h x 180v x 8-bpp mode.
    * HPLOT,x,y,color - paint a pixel of 'color' at x,y on the screen.
    * TEXTMODE - return VGA-screen back to console/text mode
    * CLS (or HOME) - clear the console/text screen.

Assumptions / Limitations:

    * HPLOT targets (only) the 320h x 180v x 8-bit-color mode of the rp6502's pico-VGA.
    * The x-coordinate from EhBasic is limited to values >= 255 (8-bits). This is a 
      limitation of parameters following the 'CALL' EhBASIC keyword.
