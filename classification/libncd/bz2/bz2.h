#ifndef _BZ2_H                                                                                                                                                           
#define _BZ2_H

#include <stdio.h>
#include <stdlib.h>

typedef struct bz2_wrapper
{
   void *strm;
} bz2_wrapper_t;

int bz2Init(bz2_wrapper_t *);
int bz2Compress(bz2_wrapper_t *, int, int, int, void *, unsigned int, void *, unsigned int *);
int bz2Decompress(bz2_wrapper_t *, int, int, void *, unsigned int, void *, unsigned int *);

#endif
