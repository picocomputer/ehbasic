/*
 *
 * file: basgraf.h
 *
 * Function headers for:
 * 
 *     init_bitmap_graphics(dimension) - Setup bitmap display; clear it. 
 *                              for either:
 *                                0x00: 320 x 180  8-bit-per-pixel
 *                                0xFF: 320 x 240  4-bit-per-pixel
 *         erase_canvas(void) - Clears the bitmapped display.
 *    draw_pixel(x, y, color) - Draws a pixel at position x,y of color
 *        init_console_text() - Setup display for console/text; clear it.
 *                      cls() - Clears the console-text display.
 *  
 * 
 *       Note: Display is much more capable than this implies. As implemented 
 *             this is the most basic code to establish the
 *             most basic graphing capability to EhBASIC on the rp6502 SBC. 
 * 
 * 
 */

#ifndef BAS_GRAF_H
#define BAS_GRAF_H

//#include <stdbool.h>
#include <stdint.h>

//#define swap(a, b) { int16_t t = a; a = b; b = t; }


//From RP6502-VGA docs: the following two macros are only needed for 16-bit color.
//Since we are limiting our BASIC colors (for now) to 8-bit, these two macros are not needed
//#define COLOR_FROM_RGB5(r,g,b) (((uint16_t)b<<11)|((uint16_t)g<<6)|((uint16_t)r))
//#define COLOR_ALPHA_MASK (1u<<5)

/* Define the 8-bit colors for 320x180 mode */
/*    to be used in the draw_pixel() call   */
#define RED     0x09
#define GREEN   0x0A
#define BLUE    0x0C
#define WHITE   0x0F

#define YELLOW  0x0B
#define CYAN    0x0E
#define MAGENTA 0x0D
#define LT_GRAY 0x07


#if 0 
/* Declare the 8-bit colors for 320x180 mode */
uint8_t black        = 0x00
uint8_t dark_gray    = 0x08
uint8_t light_gray   = 0x07
uint8_t white        = 0x0f
uint8_t red          = 0x09
uint8_t green        = 0x0a
uint8_t blue         = 0x0c
uint8_t yellow       = 0x0b
uint8_t cyan         = 0x0e
uint8_t magenta      = 0x0d
uint8_t dark_red     = 0x01
uint8_t dark_green   = 0x02
uint8_t dark_blue    = 0x04
uint8_t brown        = 0x03
uint8_t dark_cyan    = 0x06
uint8_t dark_magenta = 0x05
#endif /*notdef*/


#if 0
void init_bitmap_graphics(uint16_t canvas_struct_address,
                          uint16_t canvas_data_address,
                          uint8_t  canvas_plane,
                          uint8_t  canvas_type,
                          uint16_t canvas_width,
                          uint16_t canvas_height,
                          uint8_t  bits_per_pixel);
#endif /*0*/

/* #defines for desired screen dimension */
#define V180_H320_8BPP 0x00
#define V240_H320_4BPP 0xFF

#define HSIZE 320 /* always 320 for our use-case */
#define HMAX  ( HSIZE - 1 ) /* max x-pixel */

void init_bitmap_graphics(uint8_t dimension);
void erase_canvas(void);
void draw_pixel(uint16_t x, uint16_t y, uint16_t color);

void init_console_text(void); 
void cls(void);

//uint8_t  bits_per_pixel(void);

#endif /* BAS_GRAF_H */
