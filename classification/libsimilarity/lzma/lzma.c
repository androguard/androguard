#include "lzma.h"

#include "LzmaLib.h"

int lzmaCompress(int level, void *data, unsigned int avail_in, void *odata, unsigned int *avail_out)
{
   unsigned char outProps[5];
   unsigned int outPropsSize = 5;

   return LzmaCompress( odata, avail_out, data, avail_in, outProps, &outPropsSize, level, 0, -1, -1, -1, -1, -1 );
}
