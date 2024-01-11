; This performs a minimal set of functions the EhBASIC user
; would traditionally provide from a monitor ROM at $FF00.

.include "rp6502.inc"

.export V_INPT, V_OUTP, V_LOAD, V_SAVE
.import LAB_14BD, LAB_EVEX, LAB_XERR, LAB_22B6
.importzp Dtypef, tmp1, tmp2

fd_out:
      .byte $FF               ; output file descriptor, or negative for ACIA

V_OUTP:                       ; byte out to simulated ACIA
      BIT   fd_out            ; check for fwrite fd
      BPL   fwrite            ; use fwrite handler
V_OUTP_wait:
      BIT   RIA_READY         ; check ready bit
      BPL   V_OUTP_wait       ; wait for FIFO
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
      RTS

V_LOAD:                       ; empty load vector for EhBASIC
      RTS

V_SAVE:
      LDA #$32                ; O_TRUNC | O_CREAT | O_WRONLY
      JSR open
      STA fd_out

      JSR LAB_14BD            ; LIST

      LDA #$FF
      STA fd_out

      LDA #RIA_OP_CLOSE
      STA RIA_OP
      JMP RIA_SPIN            ; TODO check for errors

open:
      STA RIA_A
      JSR LAB_EVEX
      LDA Dtypef              ; data type flag, $FF=string, $00=numeric
	beq syntax_error
      JSR	LAB_22B6          ; pop string off descriptor stack, or from top of string
                              ; space returns with A = length, X=pointer low byte,
                              ; Y=pointer high byte
      beq syntax_error

      STX tmp1
      STY tmp2
      TAY

open_filename_copy:
      DEY
      LDA (tmp1), Y
      STA RIA_XSTACK
      TYA
      BNE open_filename_copy

      LDA #RIA_OP_OPEN
      STA RIA_OP
      JMP RIA_SPIN            ; TODO check for errors

fwrite:
      STA RIA_XSTACK
      LDA fd_out
      STA RIA_A
      LDA #RIA_OP_WRITE_XSTACK
      STA RIA_OP
fwrite_wait:
      BIT RIA_BUSY
      BMI fwrite_wait
      RTS                     ; TODO check for errors

syntax_error:
      ldx #$02                ; syntax error
      jmp LAB_XERR
