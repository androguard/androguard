#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#ifdef __cplusplus
#include <string>
#include <snappy.h>

using namespace std;

extern "C" size_t snappy_max_compressed_size(size_t length) {
   return snappy::MaxCompressedLength(length);
}

extern "C" size_t snappy_compress(const char * input, size_t input_size, char * output)
{
   string sout;
   size_t ncompbytes;

   ncompbytes = snappy::Compress(input, input_size, &sout);
   memcpy(output, sout.data(), ncompbytes);
   return ncompbytes;
}

#endif

extern "C" int snappyCompress(int level, void *data, unsigned int avail_in, void *odata, unsigned int *avail_out)
{
   size_t max_comp_size;

   max_comp_size = snappy_max_compressed_size( avail_in );
   if (max_comp_size > *avail_out) {


   }

   *avail_out = snappy_compress((char *)data, avail_in, (char *)odata);

   return 0;
}
