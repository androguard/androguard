/*cxy = len(self.compress(self.infos[x].data + self.infos[y].data))
minxy = min(self.infos[x].clen, self.infos[y].clen)
maxxy = max(self.infos[x].clen, self.infos[y].clen)

calc = float(cxy - minxy) / maxxy
*/


#include <stdio.h>
#include <string.h>

#include "./bz2/bz2.h"

#define M_BLOCK 1000000
unsigned char inbuf[M_BLOCK];

float ncd(void *orig, unsigned int size_orig, void *cmp, unsigned int size_cmp)
{
   void *joinbuff;

   unsigned int s1, s2, s3, size_join_buff, max, min, ret;

   bz2_wrapper_t bwt;
   bz2Init(&bwt);

   s1 = sizeof(inbuf);
   ret = bz2Compress(&bwt, 9, 0, 30, orig, size_orig, inbuf, &s1);
   printf("RET = %d AVAIL OUT %d\n", ret, s1);
   if (ret < 0) {

   }

   s2 = sizeof(inbuf);
   ret = bz2Compress(&bwt, 9, 0, 30, cmp, size_cmp, inbuf, &s2);
   printf("RET = %d AVAIL OUT %d\n", ret, s2);
   if (ret < 0) {
   }

   size_join_buff = size_orig + size_cmp + 1;
   joinbuff = (void *)malloc( size_join_buff );
   if (joinbuff == NULL) {

   }

   memcpy(joinbuff, orig, size_orig);
   memcpy(joinbuff+size_orig, cmp, size_cmp);

   s3 = sizeof(inbuf);
   ret = bz2Compress(&bwt, 9, 0, 30, joinbuff, size_join_buff, inbuf, &s3);
   free(joinbuff);

   printf("RET = %d AVAIL OUT %d\n", ret, s3);
   if (ret < 0) {
   }

   max = s1;
   min = s2;
   if (s2 > s1) {
      max = s2;
      min = s1;
   }

   printf("RES = %f\n", (float)(s3 - min) / max);

   return 0.0;
}

