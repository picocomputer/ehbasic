/*
 *
 * file: basgraf.c
 *
 * Functions:
 * 
 *     init_bitmap_graphics() - Setup bitmap display for 320 x 180 8-bit-per-pixel. 
 *         erase_canvas(void) - Clears the bitmapped display.
 *    draw_pixel(x, y, color) - Draws a pixel at position x,y of color
 *        init_console_text() - Setup display for console/text; clear it.
 *                      cls() - Clears the console-text display.
 * 
 * Note: Based on studying the works of:
 *        1. Vruumllc of his bitmap_graphics.c/h library and his bitmap_graphics_demo.c. 
 *        2. Rumbledethumps example-repo files: mode1.c, mode3.c and mandelbrot.c.
 *        3. Rumbledethumps Picocomputer 6502 Video Graphics Array document.
 * 
 */

#include <rp6502.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>

#include "basgraf.h"


// Parameters need when initializing the pico-VGA HW:
//   Consider if we may want any of these of global-scope.
//   Note that draw_pixel() has use for the canvas size too.

static uint16_t canvas_w = 320;     //we are enforcing 320 x 180
static uint16_t canvas_h = 180;     //we are enforcing 320 x 180

//static  uint8_t bpp_mode = 3;         /* bits_per_pixel =  8 */
//static uint16_t canvas_struct = 0xFF00;
//static uint16_t canvas_data   = 0x0000;
//static  uint8_t plane = 0;
//static  uint8_t canvas_mode = 2;



// ---------------------------------------------------------------------------
// Switch into bitmap-graphics mode, 320x180, 8-bit 256-colors, clear the screen.
// Can hook this as a 'HGR' command in EhBASIC (reference Applsoft Basic)
// ntz - in general the entire rp6502 pico-VGA is difficult to understand
// ntz - hence the comments here.
// ntz - made void of parameters to ease the c / assembly parameter-calling linkage
// ---------------------------------------------------------------------------
void init_bitmap_graphics( void /*uint16_t canvas_struct_address,
                          uint16_t canvas_data_address,
                          uint8_t  canvas_plane,
                          uint8_t  canvas_type,
                          uint16_t canvas_width,
                          uint16_t canvas_height,
                          uint8_t  bits_per_pixel */ )
{

    // initializers for the pico-VGA-HW
    uint16_t canvas_struct = 0xFF00;
    uint16_t canvas_data   = 0x0000;
    uint8_t  plane = 0;             //from RP6502-VGA docs: we have 3-planes; plane may be: 0, 1 or 2
    uint8_t  bpp_mode = 3;          /* bits_per_pixel =  8 */
    uint8_t  canvas_mode = 2;       /* 
                                     *
                                     * ntz - to-do: I am confused by the 2 vs. 3 here from vruumllc's bitmap library code
                                     *       I believe this should be a 3, not a 2; but is hard-coded 
                                     *       correctly in vruumllc's original with a 3 in the final xreg_vga_mode() call.
                                     *  
                                     * canvas_mode may be 1,2,3 or 4; I believe 0 should also be included: 
                                     *      0 - Console-mode
                                     *      1 - (Color) Character-mode
                                     *      2 - Tile-mode
                                     *      3 - Bit-mapped graphics (our case here)
                                     *      4 - Sprite-mode
                                     *                              
                                     */ 
                              
         canvas_w = 320;     //we are enforcing 320 x 180
         canvas_h = 180;     //we are enforcing 320 x 180

    /* bits_per_pixel = bpp = (2 ^ bpp_mode), for bpp_modes 0,1,2,3,4 */
    /* pico-VGA-HW needs bpp_mode, not bpp */
    /* we are only coding for our limited BASIC use case: bpp_mode-3, 8-bpp, 256-colors */
//  bpp_mode = 0; /* bits_per_pixel =  1 */
//  bpp_mode = 1; /* bits_per_pixel =  2 */
//  bpp_mode = 2; /* bits_per_pixel =  4 */
//  bpp_mode = 3; /* bits_per_pixel =  8 */  /* our case */
//  bpp_mode = 4; /* bits_per_pixel = 16 */


// Other good info to retain for possible code modifications:    
//  uint8_t x_offset = 0; //only needed for a bpp_mode=4, when initializing x_pos_px
//  uint8_t y_offset = 0; //only needed for a bpp_mode=4, when initializing y_pos_px
//  when bpp_mode==4 set x_offset = 30; /* (360 - 240)/4 */
//  when bpp_mode==4 set y_offset = 29; /* (240 - 124)/4 */


#if 0    
    // valid range check - of inputs to init_bitmap_graphics()
    if (canvas_struct_address != 0) {
        canvas_struct = canvas_struct_address;
    }
    if (canvas_data_address != 0) {
        canvas_data = canvas_data_address;
    }
    if (/*canvas_plane >= 0 &&*/ canvas_plane <= 2) {
        plane = canvas_plane;
    }
    if (canvas_type > 0 && canvas_type <= 4) {
        canvas_mode = canvas_type;
    }
    if (canvas_width > 0 && canvas_width <= 640) {
        canvas_w = canvas_width;
    }
    if (canvas_height > 0 && canvas_height <= 480) {
        canvas_h = canvas_height;
    }
#endif /*0*/


    // initialize the graphics canvas
    //
    //  note: xreg_vga_canvas( /*vargs*/ canvas_mode) is a macro that expands to:
    //        xreg(1, 0, 0,              canvas_mode)
    //
 // xreg_vga_canvas(canvas_mode);  //nzh: xreg_vga_canvas( /*canvas_mode=*/ 2 );
 // xreg_vga_canvas( /*canvas_mode=*/ 2);
    xreg(1, 0, 0, 2);

    xram0_struct_set(canvas_struct, vga_mode3_config_t, x_wrap, false);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, y_wrap, false);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, x_pos_px,    0 /*x_offset*/);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, y_pos_px,    0 /*y_offset*/);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, width_px,  320 /*canvas_w*/);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, height_px, 180 /*canvas_h*/);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, xram_data_ptr,  canvas_data);
    xram0_struct_set(canvas_struct, vga_mode3_config_t, xram_palette_ptr, 0xFFFF);

    // initialize the bitmap video modes
    //nzh: bpp_mode==3 for 8-bit-color 
    //
    //  note: xreg_vga_mode(          3, bpp_mode, canvas_struct, plane) is a macro that expands to:
    //        xreg(1, 0, 1, /*vargs*/ 3, bpp_mode, canvas_struct, plane)
    //  or simply:
    //        xreg(1, 0, 1, 3, bpp_mode, canvas_struct, plane)   
//  xreg_vga_mode(3,   bpp_mode,      canvas_struct, plane); // bitmap mode
//  xreg_vga_mode(3, /*bpp_mode=*/ 3, canvas_struct, plane); // bitmap mode
    /*ntz - note the two '3's here; the 1st 3 was hard-coded in vruumllc's code */
    xreg(1, 0, 1, 3, 3, canvas_struct, plane);


    erase_canvas(); 


} //end init_bitmap_graphics()


// ---------------------------------------------------------------------------
// Clear the 320 x 180 8-bit-color screen.
// ntz - in general the entire rp6502 pico-VGA is difficult to understand
// ntz - hence the comments here.
// ---------------------------------------------------------------------------
void erase_canvas(void)
{
    uint16_t i;
//  uint16_t num_bytes;
    uint16_t loops = 3600; 

//Note: for our BASIC special-case: canvas_w = 320 and canvas_h = 180 - always.
// pre-multiplying: num_bytes = 57600 

//    num_bytes = canvas_w * canvas_h;  //note: we may NOT want to optimize this; 
                                        //      easier to support other canvas sizes.
//    num_bytes = 57600; 

//  unrolled loop with 16 assignments needed to run num_bytes/16 = 3600 times. 

//  RIA.addr0 = canvas_data;  /*canvas_data == 0x0000 for this erase loop*/
    RIA.addr0 = 0x0000;
    RIA.step0 = 1;
//  for (i = 0; i < (num_bytes/16); i++) { /*num_bytes/16 = 3600 for our special-case*/
    for (i = 0; i < loops; i++) {
        // unrolled for speed
        RIA.rw0 = 0; /* 1*/
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0; /* 7*/
        RIA.rw0 = 0; /* 8*/
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0;
        RIA.rw0 = 0; /*16*/
    } //end for(i)

} //end erase_canvas()



// ---------------------------------------------------------------------------
// Draw a pixel on the RP6502 screen, specifically for 320 x 180 x 8bpp mode.
// Can hook this as a 'HPLOT' command in EhBASIC using existing 'CALL' keyword.
//
// ntz - This was challenging: linking the assembly-to-C parameter calling, 
// ntz -  along with deciphering EhBASIC's parameters following its 'CALL' command.
// ntz - NOTE: EhBASIC's parameters following the CALL keyword is limited to bytes only!
// ntz - This currently is limiting x pixel values to 255 or less from EhBASIC.
// ---------------------------------------------------------------------------
void draw_pixel(uint16_t x, uint16_t y, uint16_t color)
{


        /* Ensure unsigned x limited to canvas_w and unsigned y limited to canvas_h */

        x = ((x>319) ? 319 : x);
        y = ((y>179) ? 179 : y);

        //color = GREEN; //test: force green


        RIA.addr0 = canvas_w * y + x;  /* to-do: canvas_w always 320 for our special-case */
//      RIA.addr0 =      320 * y + x; 
        RIA.step0 = 1;
        RIA.rw0 = color;  //ntz - note: color is 8-bits for our limited-case; yet is a uint16_t.

} //end draw_pixel()



// ---------------------------------------------------------------------------
// Switch into console/text mode, clear the console.
// Can hook this as a 'TEXT' or 'TEXTMODE' command in EhBASIC
// ---------------------------------------------------------------------------
void init_console_text(void)
{

//  xreg_vga_mode(0); // console mode.  Macro expands to: xreg(1, 0, 1, 0);
    xreg(1, 0, 1, 0); //ntz - difficult to understand 3rd param
    xreg(1, 0, 0, 0); //ntz - diffucult to understand 4th param

    // Erase console
//  printf("\f");
    putc(0x0C, stdout);  //send a form-feed (0x0C) to the ansi-compatible VGA console; clears screen.


} //end init_console_text() 


// ---------------------------------------------------------------------------
// Clear the console.  Can hook this as a 'HOME' or 'CLS' command in EhBASIC
// ---------------------------------------------------------------------------
void cls(void)
{
    // Erase console
//  printf("\f");
    putc(0x0C, stdout);  //send a form-feed (0x0C) to the ansi-compatible VGA console; clears screen.

} //end cls()

//end-of-file
