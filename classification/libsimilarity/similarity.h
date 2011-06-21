#ifndef _LIBSIMILARITY_H
#define _LIBSIMILARITY_H

#include <stdio.h>
#include <string.h>
#include <math.h>

#include "./z/z.h"
#include "./bz2/bz2.h"
#include "./smaz/smaz.h"
#include "./lzma/lzma.h"
#include "./xz/xz.h"
#include "./snappy/snappy.h"

#define TYPE_Z          0
#define TYPE_BZ2        1
#define TYPE_SMAZ       2
#define TYPE_LZMA       3
#define TYPE_XZ         4
#define TYPE_SNAPPY     5 

struct libsimilarity {
   void *orig;
   unsigned int size_orig;
   void *cmp;
   unsigned size_cmp;

   unsigned int *corig;
   unsigned int *ccmp;

   float res;
};
typedef struct libsimilarity libsimilarity_t;

#ifdef __cplusplus
extern "C" {                                                                                                                                                                                     
    float entropy(void *, unsigned int);
    void set_compress_type(int);
    int ncd(int, libsimilarity_t *);
}
#else
void set_compress_type(int);
unsigned int compress(int, void *, unsigned int);
int ncd(int, libsimilarity_t *);
int ncs(int, libsimilarity_t *);
int cmid(int, libsimilarity_t *);
float entropy(void *, unsigned int);
#endif


#endif
