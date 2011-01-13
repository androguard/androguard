#include <stdio.h>
#include <string.h>

#include "./z/z.h"
#include "./bz2/bz2.h"
#include "./smaz/smaz.h"

#define TYPE_Z          0
#define TYPE_BZ2        1
#define TYPE_SMAZ       2

#define M_BLOCK         1000000

unsigned char inbuf[M_BLOCK];
int (*generic_Compress)(int, void *, unsigned int, void *, unsigned int *) = zCompress;

void set_compress_type(int type) {
   if (type == TYPE_Z) {
      generic_Compress = zCompress;
   } else if (type == TYPE_BZ2) {
      generic_Compress = bz2Compress;
   } else if (type == TYPE_SMAZ) {
      generic_Compress = sCompress;
   }
}

struct libncd {
   void *orig;
   unsigned int size_orig;
   void *cmp;
   unsigned size_cmp;

   unsigned int *corig;
   unsigned int *ccmp;
};

typedef struct libncd libncd_t;

float ncd(int level, libncd_t *n) 
{
   unsigned int s1, s2, s3, size_join_buff, max, min, ret;
   void *joinbuff;

   //printf("ORIG = 0x%x SIZE_ORIG = 0x%x CMP = 0x%x SIZE_CMP = 0x%x 0x%x 0x%x\n", (unsigned int)(n->orig), n->size_orig, (unsigned int)(n->cmp), n->size_cmp, *(n->corig), *(n->ccmp));

   s1 = *(n->corig);
   if (s1 == 0) {
      s1 = sizeof(inbuf);
      ret = generic_Compress(level, n->orig, n->size_orig, inbuf, &s1);
      //printf("RET = %d AVAIL OUT %d\n", ret, s1);
      if (ret < 0) {
      }

      *(n->corig) = s1;
   }

   s2 = *(n->ccmp);
   if (s2 == 0) {
      s2 = sizeof(inbuf);
      ret = generic_Compress(level, n->cmp, n->size_cmp, inbuf, &s2);
      //printf("RET = %d AVAIL OUT %d\n", ret, s2);
      if (ret < 0) {
      }
      *(n->ccmp) = s2;
   }

   size_join_buff = n->size_orig + n->size_cmp;
   joinbuff = (void *)malloc( size_join_buff );
   if (joinbuff == NULL) {
   }

   memcpy(joinbuff, n->orig, n->size_orig);
   memcpy(joinbuff+n->size_orig, n->cmp, n->size_cmp);

   s3 = sizeof(inbuf);
   ret = generic_Compress(level, joinbuff, size_join_buff, inbuf, &s3);
   free(joinbuff);

   //printf("RET = %d %d AVAIL OUT %d\n", ret, size_join_buff, s3);
   if (ret < 0) {
   }

   max = s1;
   min = s2;
   if (s2 > s1) {
      max = s2;
      min = s1;
   }

   return (float)(s3 - min) / max;
}

