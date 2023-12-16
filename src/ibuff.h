#ifndef _IBUFF_H_
#define _IBUFF_H_

extern void _RAM_START__, _RAM_SIZE__, _STACKSIZE__, _IBUFFSIZE__;
#define Ibuffs (char *)((unsigned)&_RAM_START__ + (unsigned)&_RAM_SIZE__ + (unsigned)&_STACKSIZE__)
#define Ibuffe (Ibuffs + (unsigned)&_IBUFFSIZE__)

#endif /* _IBUFF_H_ */
