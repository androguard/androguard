#include "bz2.h"

#include <bzlib.h>

int bz2Init(bz2_wrapper_t *bwt)
{
   bwt->strm = malloc(sizeof(bz_stream));
   return 0;
}

int bz2Compress(bz2_wrapper_t *bwt, int blockSize100k, int verbosity, int workFactor, void *data, unsigned int avail_in, void *odata, unsigned int *avail_out)
{
   int ret;
   bz_stream *strm = bwt->strm;

   strm->bzalloc = NULL;
   strm->bzfree = NULL;   
   strm->opaque = NULL;

   ret = BZ2_bzCompressInit(strm, blockSize100k, verbosity, workFactor);
   if (ret != BZ_OK) return ret;

   strm->next_in = data;
   strm->next_out = odata;
   strm->avail_in = avail_in;
   strm->avail_out = *avail_out;

   ret = BZ2_bzCompress ( strm, BZ_FINISH );
   if (ret == BZ_FINISH_OK) goto output_overflow;
   if (ret != BZ_STREAM_END) goto errhandler;
   
   /* normal termination */   
   *avail_out -= strm->avail_out;
   BZ2_bzCompressEnd ( strm );                                                                                                                                                    
   return BZ_OK;
   
   output_overflow:
      BZ2_bzCompressEnd ( strm );      
      return BZ_OUTBUFF_FULL;

                     
   errhandler:   
      BZ2_bzCompressEnd ( strm );

   return ret;
}

int bz2Decompress(bz2_wrapper_t *bwt, int small, int verbosity, void *data, unsigned int avail_in, void *odata, unsigned int *avail_out)
{
   int ret;
   bz_stream *strm = bwt->strm;

   strm->bzalloc = NULL;
   strm->bzfree = NULL;   
   strm->opaque = NULL;
   
   ret = BZ2_bzDecompressInit ( strm, verbosity, small );
   if (ret != BZ_OK) return ret;

 
   strm->next_in = data; 
   strm->next_out = odata;    
   strm->avail_in = avail_in;       
   strm->avail_out = *avail_out;
   
   ret = BZ2_bzDecompress ( strm );      
   if (ret == BZ_OK) goto output_overflow_or_eof;         
   if (ret != BZ_STREAM_END) goto errhandler;

               
   /* normal termination */   
   *avail_out -= strm->avail_out;               
   BZ2_bzDecompressEnd ( strm );                  
   return BZ_OK;

                        

output_overflow_or_eof:
   if (strm->avail_out > 0) {            
               BZ2_bzDecompressEnd ( strm );               
               return BZ_UNEXPECTED_EOF;                                             
   } else {
               BZ2_bzDecompressEnd ( strm );
               return BZ_OUTBUFF_FULL;               
   };      

                           
errhandler:
   BZ2_bzDecompressEnd ( strm );           
   return ret; 
}
