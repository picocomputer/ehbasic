; Instead of "6502 EhBASIC [C]old/[W]arm ?"
; Use CTRL-ALT-DEL then RESET for warm start.
; Load the virtual ROM again for a cold start.

; void main(void);

.export _main

.importzp LAB_WARM
.import LAB_COLD

.proc _main
      CLC                     ; Modifies to SEC after first run
      BCC   AutoCold
      JMP   LAB_WARM          ; do EhBASIC warm start
AutoCold:
      LDA   #$38              ; SEC
      STA   _main             ; self-modify
      JMP   LAB_COLD          ; do EhBASIC cold start
.endproc
