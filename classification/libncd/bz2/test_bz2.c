#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "bz2.h"

#define LEN 30
#define LEN2 LEN*2

#define STRING1 "TOTO TOTO"

void hexdump(unsigned char * data, unsigned int amount, size_t addr)
{
  unsigned int dp;
  unsigned int p;
  const char trans[] =
    "................................ !\"#$%&'()*+,-./0123456789"
    ":;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklm"
    "nopqrstuvwxyz{|}~...................................."
    "....................................................."
    "........................................";

  for ( dp = 1; dp <= amount; dp++ )
    {
      if ( (dp % 16) == 1 )
        {
          fprintf( stdout, "%#08x | ", addr+dp-1 );
        }

      fprintf( stdout, "%02x ", data[dp-1] );
      if ( (dp % 8) == 0 && (dp % 16) != 0 )
        {
          fputs( " ", stdout );
        }
      if ( (dp % 16) == 0 )
        {
          fputs( "| ", stdout );
          p = dp;
          for ( dp -= 16; dp < p; dp++ )
            {
              fprintf( stdout, "%c", trans[data[dp]] );
            }
          fputs( "\n", stdout );
        }
    }

  if ( (amount % 16) != 0 )
    {
      p = dp = 16 - ( amount % 16 );
      for ( dp = p; dp > 0; dp-- )
        {
          fputs( "   ", stdout );
          if ( ((dp % 8) == 0) && (p != 8) )
            {
              fputs( " ", stdout );
            }
        }
      fputs( "| ", stdout );
      for ( dp = (amount - (16 - p)); dp < amount; dp++ ) {
        fprintf( stdout, "%c", trans[data[dp]] );
      }
    }

  fputs( "\n", stdout );
  return;
}    

int main(int argc, char *argv[])
{
   unsigned char data[LEN], data2[LEN2], data3[LEN2];
   unsigned int avail_out, avail_out2;
   int ret;

   bz2_wrapper_t bwt;

   memset(data, 0, sizeof(data));
   memset(data2, 0, sizeof(data2));
   memset(data3, 0, sizeof(data3));                                                                                                                                       

   memcpy(data, STRING1, strlen(STRING1));

   avail_out = sizeof(data2);

   bz2Init(&bwt);

   ret = bz2Compress(&bwt, 9, 0, 30, data, strlen(STRING1), data2, &avail_out);
   printf("RET = %d AVAIL OUT %d\n", ret, avail_out);
   hexdump(data, sizeof(data), (size_t)data);
   hexdump(data2, sizeof(data2), (size_t)data2);

   avail_out2 = sizeof(data3);
   ret = bz2Decompress(&bwt, 0, 0, data2, avail_out, data3, &avail_out2);  
   printf("RET = %d AVAIL_OUT %d\n", ret, avail_out2);     
   hexdump(data2, sizeof(data2), (size_t)data2);   
   hexdump(data3, sizeof(data3), (size_t)data3);

   return 0;
}
