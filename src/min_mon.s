.include "rp6502.inc"
.include "zp.inc"

; void min_mon(void);

.export _min_mon
.export V_INPT, V_OUTP, V_LOAD, V_SAVE

.import LAB_COLD, VEC_IN

; Instead of "6502 EhBASIC [C]old/[W]arm ?"
; Use CTRL-ALT-DEL then RESET for warm start.
; Load the virtual ROM again for a cold start.

_min_mon:
      CLC                     ; Modifies to SEC after first run
      BCC   AutoCold
      JMP   LAB_WARM          ; do EhBASIC warm start

AutoCold:
      LDA   #$38              ; SEC
      STA   _min_mon          ; self-modify

      LDA   #<IRQ_CODE        ; Setup 6502 IRQ Vector
      STA   $FFFE
      LDA   #>IRQ_CODE
      STA   $FFFF

      LDA   #<NMI_CODE        ; Setup 6502 NMI vector
      STA   $FFFA
      LDA   #>NMI_CODE
      STA   $FFFB

      JMP   LAB_COLD          ; do EhBASIC cold start

; EhBASIC IRQ support

IRQ_CODE:
      PHA                     ; save A
      LDA   IrqBase           ; get the IRQ flag byte
      LSR                     ; shift the set b7 to b6, and on down ...
      ORA   IrqBase           ; OR the original back in
      STA   IrqBase           ; save the new IRQ flag byte
      PLA                     ; restore A
      RTI

; EhBASIC NMI support

NMI_CODE:
      PHA                     ; save A
      LDA   NmiBase           ; get the NMI flag byte
      LSR                     ; shift the set b7 to b6, and on down ...
      ORA   NmiBase           ; OR the original back in
      STA   NmiBase           ; save the new NMI flag byte
      PLA                     ; restore A
      RTI

; byte out to simulated ACIA

V_OUTP:
      BIT   RIA_READY
      BPL   V_OUTP            ; wait for FIFO

      STA   RIA_TX            ; save byte to simulated ACIA
      RTS

; byte in from simulated ACIA

V_INPT:

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
