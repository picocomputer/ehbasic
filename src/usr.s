; See EhBASIC-manual.pdf "using USR()" to learn about what can go here.

.include "rp6502.inc"

.export V_USR
.import LAB_FCER
.import F_HGR, F_HPLOT, F_TEXT, F_CLS 

V_USR:
      JMP LAB_FCER            ; Replace me with your code ("Function call" error)

NewFunc_Tab:
      .word F_CLS             ; new HOME (or CLS) command -> _cls command 
      .word F_TEXT            ; new TEXTMODE -> _init_console_text() command
      .word F_HGR             ; new HGR -> _init_bitmap_graphics() command
      .word F_HPLOT           ; new HPLOT,x,y,color command
EndNfTab:
