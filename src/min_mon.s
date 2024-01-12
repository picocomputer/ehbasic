; This performs a minimal set of functions the EhBASIC user
; would traditionally provide from a monitor ROM at $FF00.

.include "rp6502.inc"

.export V_INPT, V_OUTP, V_LOAD, V_SAVE
.import LAB_14BD, LAB_EVEX, LAB_SNER, LAB_22B6
.importzp Dtypef, ptr1

.data

fd_out:
      .byte $FF               ; output file descriptor, or negative for ACIA

.code

V_OUTP:                       ; byte out to simulated ACIA
      BIT   fd_out            ; check for fwrite fd
      BPL   write             ; use fwrite handler
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
      LDA   #$32              ; O_TRUNC | O_CREAT | O_WRONLY
      JSR   open
      BMI   syntax_error      ; TODO file error instead of syntax
      STA   fd_out            ; redirect V_OUTP to fd
      JSR   LAB_14BD          ; LIST
      LDA   fd_out
      STA   RIA_A             ; to be used by close()
      LDA   #$FF
      STA   fd_out            ; restore V_OUTP to ACIA
      LDA   #RIA_OP_CLOSE
      STA   RIA_OP            ; int close(int fildes)
      JSR   RIA_SPIN
      BMI   syntax_error      ; TODO file error instead of syntax
      RTS

open:
      STA   RIA_A             ; file open options
      JSR   LAB_EVEX          ; evaluate expression
      LDA   Dtypef            ; data type flag, $FF=string, $00=numeric
      BEQ   syntax_error      ; syntax error if not string
      JSR   LAB_22B6          ; obtain string
      STX   ptr1              ; pointer low byte
      STY   ptr1+1            ; pointer high byte
      TAY                     ; length
      BEQ   syntax_error      ; syntax error if  empty string

push_filename:
      DEY
      LDA   (ptr1), Y
      STA   RIA_XSTACK
      TYA
      BNE   push_filename

      LDA   #RIA_OP_OPEN
      STA   RIA_OP            ; int open(const char *path, int oflag)
      JMP   RIA_SPIN

syntax_error:
      jmp   LAB_SNER          ; far jump

write:
      STA   RIA_XSTACK
      LDA   fd_out
      STA   RIA_A
      LDA   #RIA_OP_WRITE_XSTACK
      STA   RIA_OP            ; int write_xstack(const void *buf, unsigned count, int fildes)
write_busy:
      BIT   RIA_BUSY
      BMI   write_busy
      RTS                     ; TODO check for errors
