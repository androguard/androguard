#ifndef _BZ2_H                                                                                                                                                           
#define _BZ2_H

#include <stdio.h>
#include <stdlib.h>

int zCompress(int, int, int, void *, unsigned int, void *, unsigned int *);
int zDecompress(int, int, void *, unsigned int, void *, unsigned int *);

#endif
