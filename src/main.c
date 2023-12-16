#include <stdlib.h>

extern void min_mon(void);                  /* min_mon.s */
extern void LAB_1B5B_CALL1, LAB_1B5B_CALL2; /* basic.s */

void main()
{
    /* EhBASIC has restrictions on certain memory locations. */
    /* Refuse to run if these fail. */
    if (((unsigned)&LAB_1B5B_CALL1 & 0xFF) == 0xFD ||
        ((unsigned)&LAB_1B5B_CALL2 & 0xFF) == 0xFD)
        exit(1);

    /* Start EhBASIC from its "monitor" */
    min_mon();
}
