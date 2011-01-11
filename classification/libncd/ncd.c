/*cxy = len(self.compress(self.infos[x].data + self.infos[y].data))
minxy = min(self.infos[x].clen, self.infos[y].clen)
maxxy = max(self.infos[x].clen, self.infos[y].clen)

calc = float(cxy - minxy) / maxxy
*/


#include <stdio.h>
#include <string.h>

#include "./z/z.h"
#include "./bz2/bz2.h"

#define TYPE_Z 0
#define TYPE_BZ2 1

#define M_BLOCK 1000000

unsigned char inbuf[M_BLOCK];
int (*generic_Compress)(int, int, int, void *, unsigned int, void *, unsigned int *) = zCompress;

void set_compress_type(int type) {
   if (type == TYPE_Z) {
      generic_Compress = zCompress;
   } else if (type == TYPE_BZ2) {
      generic_Compress = bz2Compress;
   }
}

float ncd(void *orig, unsigned int size_orig, void *cmp, unsigned int size_cmp)
{
   void *joinbuff;

   unsigned int s1, s2, s3, size_join_buff, max, min, ret;

   s1 = sizeof(inbuf);
   ret = generic_Compress(9, 0, 30, orig, size_orig, inbuf, &s1);
   //printf("RET = %d AVAIL OUT %d\n", ret, s1);
   if (ret < 0) {
   }

   s2 = sizeof(inbuf);
   ret = generic_Compress(9, 0, 30, cmp, size_cmp, inbuf, &s2);
   //printf("RET = %d AVAIL OUT %d\n", ret, s2);
   if (ret < 0) {
   }

   size_join_buff = size_orig + size_cmp;
   joinbuff = (void *)malloc( size_join_buff );
   if (joinbuff == NULL) {
   }

   memcpy(joinbuff, orig, size_orig);
   memcpy(joinbuff+size_orig, cmp, size_cmp);

   s3 = sizeof(inbuf);
   ret = generic_Compress(9, 0, 30, joinbuff, size_join_buff, inbuf, &s3);
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

