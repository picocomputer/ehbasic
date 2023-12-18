.include "rp6502.inc"
.include "zp.inc"

; void main(void); // for RP6502

.export _main

.import LAB_COLD

; Instead of "6502 EhBASIC [C]old/[W]arm ?"
; Use CTRL-ALT-DEL then RESET for warm start.
; Load the virtual ROM again for a cold start.

.proc _main
      CLC                     ; Modifies to SEC after first run
      BCC   AutoCold
      JMP   LAB_WARM          ; do EhBASIC warm start
AutoCold:
      LDA   #$38              ; SEC
      STA   _main             ; self-modify
      JMP   LAB_COLD          ; do EhBASIC cold start
.endproc
