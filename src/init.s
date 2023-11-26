.export _init

; put the IRQ and MNI code in RAM so that it can be changed

IRQ_vec     = VEC_SV+2        ; IRQ code vector
NMI_vec     = IRQ_vec+$0A     ; NMI code vector

_init:
      CLD                     ; clear decimal mode
      LDX   #$FF              ; empty stack
      TXS                     ; set the stack

; set up vectors and interrupt code, copy them to page 2

      LDY   #END_CODE-LAB_vec ; set index/count
LAB_stlp:
      LDA   LAB_vec-1,Y       ; get byte from interrupt code
      STA   VEC_IN-1,Y        ; save to RAM
      DEY                     ; decrement index/count
      BNE   LAB_stlp          ; loop if more to do

; Automate "6502 EhBASIC [C]old/[W]arm ?"
; Use CTRL-ALT-DEL then RESET for warm start.
; Load the virtual ROM again for a cold start.

LAB_signon:
      CLC                     ; Modifies to SEC after first run
      BCC   AutoCold
      JMP   LAB_WARM          ; do EhBASIC warm start

AutoCold:
      LDA   #$38              ; SEC
      STA   LAB_signon
      JMP   LAB_COLD          ; do EhBASIC cold start

; byte out to simulated ACIA

ACIAout:
      BIT   RIA_READY
      BPL   ACIAout           ; wait for FIFO

      STA   RIA_TX            ; save byte to simulated ACIA
      RTS

; byte in from simulated ACIA

ACIAin:

      BIT   RIA_READY
      BVC   LAB_nobyw         ; branch if no byte waiting

      LDA   RIA_RX            ; get byte from simulated ACIA
      SEC                     ; flag byte received
      RTS

LAB_nobyw:
      CLC                     ; flag no byte received
no_load:                      ; empty load vector for EhBASIC
no_save:                      ; empty save vector for EhBASIC
      RTS

; vector tables

LAB_vec:
      .word ACIAin            ; byte in from simulated ACIA
      .word ACIAout           ; byte out to simulated ACIA
      .word no_load           ; null load vector for EhBASIC
      .word no_save           ; null save vector for EhBASIC

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

END_CODE:
