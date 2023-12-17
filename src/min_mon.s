.include "rp6502.inc"
.include "zp.inc"

; This performs a minimal set of functions the EhBASIC user
; would traditionally provide from a monitor ROM at $FF00.

; void min_mon(void); // for RP6502

.export _min_mon
.export V_INPT, V_OUTP, V_LOAD, V_SAVE

.import LAB_COLD, VEC_IN

; Instead of "6502 EhBASIC [C]old/[W]arm ?"
; Use CTRL-ALT-DEL then RESET for warm start.
; Load the virtual ROM again for a cold start.

.segment "CODE"

_min_mon:
      CLC                     ; Modifies to SEC after first run
      BCC   AutoCold
      JMP   LAB_WARM          ; do EhBASIC warm start
AutoCold:
      LDA   #$38              ; SEC
      STA   _min_mon          ; self-modify
      JMP   LAB_COLD          ; do EhBASIC cold start

V_OUTP:                       ; byte out to simulated ACIA
      BIT   RIA_READY
      BPL   V_OUTP            ; wait for FIFO
      STA   RIA_TX            ; save byte to simulated ACIA
      RTS
V_INPT:                       ; byte in from simulated ACIA
      BIT   RIA_READY
      BVC   LAB_nobyw         ; branch if no byte waiting
      LDA   RIA_RX            ; get byte from simulated ACIA
      SEC                     ; flag byte received
      RTS
LAB_nobyw:
      CLC                     ; flag no byte received
V_LOAD:                       ; empty load vector for EhBASIC
V_SAVE:                       ; empty save vector for EhBASIC
      RTS


; Memory size in basic.cfg must match this HEADER segment exactly.
; This HEADER segment is always in a known location to allow for
; setting the vectors with rp6502_executable in CMakeLists.txt.

.segment "HEADER"

; RESET vector $C000:

      BRA   ProgStart         ; jmp to the program start

; IRQ vector $C002:

      PHA                     ; save A
      LDA   IrqBase           ; get the IRQ flag byte
      LSR                     ; shift the set b7 to b6, and on down ...
      ORA   IrqBase           ; OR the original back in
      STA   IrqBase           ; save the new IRQ flag byte
      PLA                     ; restore A
      RTI

; NMI vector $C00C:

      PHA                     ; save A
      LDA   NmiBase           ; get the NMI flag byte
      LSR                     ; shift the set b7 to b6, and on down ...
      ORA   NmiBase           ; OR the original back in
      STA   NmiBase           ; save the new NMI flag byte
      PLA                     ; restore A
      RTI

ProgStart:
