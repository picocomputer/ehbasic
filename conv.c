#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

int main()
{
    FILE *in, *oarr;
    in = fopen("a.out", "r");
    if (NULL == in)
    {
        printf("File a.out can't be opened\n");
        exit(1);
    }
    oarr = fopen("basic.c", "w");
    if (NULL == oarr)
    {
        printf("File basic.c can't be written\n");
        exit(1);
    }

    int addr = fgetc(in) + (fgetc(in) << 8);
    fprintf(oarr, "char basic[] = { // $%4X\n", addr);

    int ch;
    while (true)
    {
        ch = fgetc(in);
        if (EOF == ch)
            break;
        fprintf(oarr, "0x%02X,", ch);
        if (++addr & 0xF)
            fprintf(oarr, " ");
        else
            fprintf(oarr, "\n");
    }

    fprintf(oarr, "};\n");
    fclose(oarr);
    fclose(in);
    return 0;
}
