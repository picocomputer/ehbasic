.include "rp6502.inc"
.include "zp.inc"

; This performs a minimal set of functions the EhBASIC user
; would traditionally provide from a monitor ROM at $FF00.

.export V_INPT, V_OUTP, V_LOAD, V_SAVE

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
