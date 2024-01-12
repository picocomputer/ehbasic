; This performs a minimal set of functions the EhBASIC user
; would traditionally provide from a monitor ROM at $FF00.

.include "rp6502.inc"

.export V_INPT, V_OUTP, V_LOAD, V_SAVE
.import LAB_14BD, LAB_EVEX, LAB_SNER, LAB_22B6, LAB_1463, LAB_RMSG
.importzp Dtypef, ptr1, tmp1

.data

fd_in:
      .byte $FF               ; input file descriptor, or negative for ACIA
fd_out:
      .byte $FF               ; output file descriptor, or negative for ACIA

.code

V_INPT:                       ; byte in from simulated ACIA
      BIT   fd_in             ; check for read fd
      BPL   read              ; use read() handler
      BIT   RIA_READY
      BVC   LAB_nobyw         ; branch if no byte waiting
      LDA   RIA_RX            ; get byte from simulated ACIA
      SEC                     ; flag byte received
      RTS
LAB_nobyw:
      CLC                     ; flag no byte received
      RTS
read:
      LDA   tmp1
      BEQ   read_read
      DEC   tmp1
      LDA   #$0D
      SEC
      RTS
read_read:
      LDA   #$01
      STA   RIA_XSTACK
      LDA   fd_in
      STA   RIA_A
      LDA   #RIA_OP_READ_XSTACK
      STA   RIA_OP            ; int read_xstack(void *buf, unsigned count, int fildes)
read_busy:
      BIT   RIA_BUSY
      BMI   read_busy
      LDA   RIA_XSTACK
      CMP   #$0A              ; LF and CRLF endings supported
      BEQ   read_cr
      CMP   #$00              ; empty stack always returns 0
      BNE   read_done
      LDA   fd_in             ; eof
      STA   RIA_A
      LDA   #RIA_OP_CLOSE
      STA   RIA_OP            ; int close(int fildes)
read_close:
      BIT   RIA_BUSY
      BMI   read_close
      LDA   #$FF
      STA   fd_in             ; restore V_INPT to ACIA
      STA   fd_out            ; restore V_OUTP to ACIA
      PHY                     ; print "Ready"
      LDA   #<(LAB_RMSG)
      STA   ptr1
      LDA   #>(LAB_RMSG)
      STA   ptr1+1
      LDY   #$00
read_ready_loop:
      LDA   (ptr1),y
      JSR   V_OUTP_wait
      INY
      CPY   #$07
      BMI   read_ready_loop
      PLY
read_cr:
      LDA   #$0D
read_done:
      SEC
      RTS


V_OUTP:                       ; byte out to simulated ACIA
      BIT   fd_out            ; check for write fd
      BPL   write             ; use write() handler
V_OUTP_wait:
      BIT   RIA_READY         ; check ready bit
      BPL   V_OUTP_wait       ; wait for FIFO
      STA   RIA_TX            ; save byte to simulated ACIA
      RTS
write:
      BIT   fd_in             ; check for read fd
      BPL   write_skip        ; dump load echos to null
      CMP   #$0D              ; ASCII 13 CR
      BEQ   write_skip        ; filter CR, saves are LF only
      STA   RIA_XSTACK
      LDA   fd_out
      STA   RIA_A
      LDA   #RIA_OP_WRITE_XSTACK
      STA   RIA_OP            ; int write_xstack(const void *buf, unsigned count, int fildes)
write_busy:
      BIT   RIA_BUSY
      BMI   write_busy        ; TODO check for errors
write_skip:
      RTS


V_LOAD:                       ; empty load vector for EhBASIC
      LDA   #$01              ; O_RDONLY
      JSR   open
      BMI   syntax_error      ; TODO file error instead of syntax
      STA   fd_in             ; redirect V_INPT from fd
      STA   fd_out            ; redirect V_OUTP to null
      TSX                     ; LAB_NEW clobbers stack, save the return
      INX
      LDA   $100,X
      STA   ptr1
      INX
      LDA   $100,X
      STA   ptr1+1
      JSR   LAB_1463          ; LAB_NEW
      LDA   ptr1+1            ; restore the return address clobbered by new
      PHA
      LDA   ptr1
      PHA
      LDA   #$01              ; preamble newlines
      STA   tmp1
      RTS


V_SAVE:
      LDA   #$32              ; O_TRUNC | O_CREAT | O_WRONLY
      JSR   open
      BMI   syntax_error      ; TODO file error instead of syntax
      STA   fd_out            ; redirect V_OUTP to fd
      JSR   LAB_14BD          ; LAB_LIST
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
      BEQ   syntax_error      ; syntax error if empty string
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
      JMP   LAB_SNER          ; far jump
