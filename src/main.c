#include <rp6502.h>
#include <stdlib.h>

extern void min_mon(void);
extern void LAB_1B5B_CALL1(void);
extern void LAB_1B5B_CALL2(void);

void main()
{
    // EhBASIC has restrictions on certain memory locations.
    // Refuse to run if these fail.
    if (((int)LAB_1B5B_CALL1 & 0xFF) == 0xFD ||
        ((int)LAB_1B5B_CALL2 & 0xFF) == 0xFD)
        exit(1);

    // Start EhBASIC from its "monitor"
    min_mon();
}
