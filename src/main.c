#include <rp6502.h>
#include <stdlib.h>

extern void min_mon(void);
extern void LAB_1B5B_CALL1(void);
extern void LAB_1B5B_CALL2(void);

void main()
{
    // This replaces patch 2.22p5.3
    // until a better solution is found
    if (((int)LAB_1B5B_CALL1 & 0xFF) == 0xFD ||
        ((int)LAB_1B5B_CALL2 & 0xFF) == 0xFD)
        exit(1);

    // Start EhBASIC from its "monitor"
    min_mon();
}
