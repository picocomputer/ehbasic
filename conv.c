#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

int main()
{
    FILE *in, *ohex, *oarr;
    in = fopen("a.out", "r");
    if (NULL == in)
    {
        printf("File a.out can't be opened\n");
        exit(1);
    }
    ohex = fopen("basic.hex", "w");
    if (NULL == ohex)
    {
        printf("File basic.hex can't be written\n");
        exit(1);
    }
    oarr = fopen("basic.c", "w");
    if (NULL == ohex)
    {
        printf("File basic.c can't be written\n");
        exit(1);
    }


    int addr = fgetc(in) + (fgetc(in) << 8);
    bool sol = true;

    fprintf(oarr, "char basic[] = { // $%4X\n", addr);

    int ch;
    while (true)
    {
        ch = fgetc(in);
        if (EOF == ch)
            break;
        if (sol)
            fprintf(ohex, "%4X:", addr);
        fprintf(oarr, "0x%02X,", ch);
        fprintf(ohex, " %02X", ch);
        if (++addr & 0xF)
        {
            sol = false;
            fprintf(oarr, " ");
        }
        else
        {
            sol = true;
            fprintf(oarr, "\n");
            fprintf(ohex, "\n");
            if (!(addr & 0xFFF))
                fprintf(ohex, "\n");
        }
    }

    fprintf(oarr, "};\n");
    fclose(ohex);
    fclose(in);
    return 0;
}
