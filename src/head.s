.include "rp6502.inc"
.include "zp.inc"

; Memory size in basic.cfg must match this HEAD segment exactly.
; This HEAD segment is always in a known location to allow for
; setting the vectors with rp6502_executable in CMakeLists.txt.

.segment "HEAD"

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
