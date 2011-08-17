/* 
 This file is part of Androguard.

 Copyright (C) 2011, Anthony Desnos <desnos at t0t0.fr>
 All rights reserved.

 Androguard is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Androguard is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of  
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public License
 along with Androguard.  If not, see <http://www.gnu.org/licenses/>.
*/
#include <Python.h>

#ifdef __cplusplus

#include <iostream>
#include <google/sparse_hash_map>
#include <hash_map>
#include <string>
#include <vector>

//#include "dvm_header.pb.h"

using namespace __gnu_cxx;
using namespace std;
using google::sparse_hash_map;      // namespace where class lives by default
using std::cout;
using std::endl;

struct debug {
};

typedef struct debug debug_t;

void hexdump(void *pAddressIn, long  lSize)
{
 char szBuf[100];
 long lIndent = 1;
 long lOutLen, lIndex, lIndex2, lOutLen2;
 long lRelPos;
 struct { char *pData; unsigned long lSize; } buf;
 unsigned char *pTmp,ucTmp;
 unsigned char *pAddress = (unsigned char *)pAddressIn;

   buf.pData   = (char *)pAddress;
   buf.lSize   = lSize;

   while (buf.lSize > 0)
   {
      pTmp     = (unsigned char *)buf.pData;
      lOutLen  = (int)buf.lSize;
      if (lOutLen > 16)
          lOutLen = 16;

      // create a 64-character formatted output line:
      sprintf(szBuf, " >                            "
                     "                      "
                     "    %08lX", (unsigned long)(pTmp-pAddress));
      lOutLen2 = lOutLen;

      for(lIndex = 1+lIndent, lIndex2 = 53-15+lIndent, lRelPos = 0;
          lOutLen2;
          lOutLen2--, lIndex += 2, lIndex2++
         )
      {
         ucTmp = *pTmp++;

         sprintf(szBuf + lIndex, "%02X ", (unsigned short)ucTmp);
         if(!isprint(ucTmp))  ucTmp = '.'; // nonprintable char
         szBuf[lIndex2] = ucTmp;

         if (!(++lRelPos & 3))     // extra blank after 4 bytes
         {  lIndex++; szBuf[lIndex+2] = ' '; }
      }

      if (!(lRelPos & 3)) lIndex--;

      szBuf[lIndex  ]   = '<';
      szBuf[lIndex+1]   = ' ';

      printf("%s\n", szBuf);

      buf.pData   += lOutLen;
      buf.lSize   -= lOutLen;
   }
}



class Buff {
    public :
        const char *bdata;
        size_t bdata_len;
        size_t bcurrent_idx;

        vector<unsigned long *> DynamicOffsets;
    public :
        Buff() {

        }

        Buff(const char *data, size_t data_len) {
            bdata = data;
            bdata_len = data_len;
            bcurrent_idx = 0;
        }
        
        Buff(const char *data, size_t data_len, size_t current_idx) {
            bdata = data;
            bdata_len = data_len;
            bcurrent_idx = current_idx;
        }
        
        void setup(const char *data, size_t data_len, size_t current_idx) {
            bdata = data;
            bdata_len = data_len;
            bcurrent_idx = current_idx;
        }

        const char *read(size_t len) {
            //cout << "read add " << bcurrent_idx << " " << len << "\n";
            bcurrent_idx += len;
            return (bdata + (bcurrent_idx - len));
        }
        
        const char *readat(size_t pos, size_t len) {
            return (bdata + (pos));
        }

        const char *read_false(size_t len) {
            return (bdata + (bcurrent_idx));
        }

        size_t get_current_idx() {
            return bcurrent_idx;
        }

        size_t get_end() {
            return bdata_len;
        }

        bool empty() {
            return bcurrent_idx == bdata_len;
        }


        int register_dynamic_offset(unsigned long *addr) {
            DynamicOffsets.push_back( addr );
        }
};

/*
HEADER_NAMEDTUPLE = namedtuple( "HEADER_NAMEDTUPLE", "magic checksum signature file_size header_size endian_tag link_size link_off " \
                                                             "map_off string_ids_size string_ids_off type_ids_size type_ids_off proto_ids_size " \
                                                                                                                  "proto_ids_off field_ids_size field_ids_off method_ids_size method_ids_off "\
                                                                                                                  "class_defs_size class_defs_off data_size data_off" )
HEADER = [ '=QL20sLLLLLLLLLLLLLLLLLLLL', HEADER_NAMEDTUPLE ]
*/
typedef struct IHeader {
    unsigned char magic[8];
    unsigned long checksum;
    unsigned char signature[20];
    unsigned long file_size;
    unsigned long header_size;
    unsigned long endian_tag;
    unsigned long link_size;
    unsigned long link_off;
    unsigned long map_off;
    unsigned long string_ids_size;
    unsigned long string_ids_off;
    unsigned long type_ids_size;
    unsigned long type_ids_off;
    unsigned long proto_ids_size;
    unsigned long proto_ids_off;
    unsigned long field_ids_size;
    unsigned long field_ids_off;
    unsigned long method_ids_size;
    unsigned long method_ids_off;
    unsigned long class_defs_size;
    unsigned long class_defs_off;
    unsigned long data_size;
    unsigned long data_off;
} IHeader_t;


class Basic {
    public :
        Buff *bb;
    public :
        Basic( Buff *b ) {
             bb = b;
        }

        int setup( void *elem, size_t len_elem ) {
            memcpy( elem, bb->read( len_elem ), len_elem );
        }
        
        int setup_false( void *elem, size_t len_elem ) {
            memcpy( elem, bb->read_false( len_elem ), len_elem );
        }
/*
        template <class T> int setup_obj( T &elem, size_t nb ) {

        }
*/
};

class Header : public Basic {
    public :
        IHeader_t ih;

    public :
        Header(Buff *b) : Basic( b ) { 
            /* setup header structure */
            setup( &ih, sizeof(IHeader_t) );
            /*
            memcpy( &isize, b.read(4), 4);
            memset(&ih, '\0', sizeof(IHeader_t));
            memcpy( &ih, b.read(sizeof(IHeader_t)), sizeof(IHeader_t) );
            */
            hexdump( &ih, sizeof( IHeader_t ) );

        //    b.register_dynamic_offset( &ih.link_off );
        }

        int set_magic(unsigned char *magic, size_t len) {
            return 0;
        }

        int set_checksum(unsigned long checksum) {
            return 0;
        }

        string get_raw() {
            string s = string( (const char *)&ih, sizeof(IHeader_t) );
            return s;
        }
};

/*
 * MAP_ITEM_NAMEDTUPLE = namedtuple("MAP_ITEM_NAMEDTUPLE", "type unused size offset")
 * MAP_ITEM = [ '=HHLL', MAP_ITEM_NAMEDTUPLE ]
 */
typedef struct IMapItem {
    unsigned short type;
    unsigned short unused;
    unsigned long size;
    unsigned long offset;
} IMapItem_t;

class MapItem : public Basic {
    public :
        IMapItem imi;
    public :
        MapItem(Buff *b) : Basic( b ) {
            setup( &imi, sizeof(IMapItem_t) );
            
            cout << imi.type <<  " " << imi.size << "\n";
            exit(0);
        }

        string get_raw() {

        }
};

class MapList : public Basic {
    public :
       unsigned long isize;
       vector<MapItem> iMapItems;

    public :
        MapList(Buff *b) : Basic( b ) {
            setup( &isize, 4 );
            cout << "size " << isize << "\n";
            //setup_obj( &MapItem, isize );
            for(int i=0; i < isize; i++) {
                iMapItems.push_back( MapItem( b ) );
            }
        }

        int set_size(unsigned long size) {
            isize = size;
        }

        string &get_raw() {
            string *s = new string();

            /* add size */


            /* add mapitems */
            for(int ii=0; ii < iMapItems.size(); ii++) { 
                *s += iMapItems[ ii ].get_raw();
            }

            return *s;
        }
};

unsigned long B_A_OP_CCCC(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    unsigned short *si16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    //memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    //memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)i16 );

    return 4;
}

const unsigned long OPVALUE = 0;
const unsigned long REGISTER = 1;
const unsigned long FIELD = 2;
const unsigned long METHOD = 3;
const unsigned long TYPE = 4;
const unsigned long INTEGER = 5;
const unsigned long STRING = 6;

unsigned long B_A_OP_CCCC_3_FIELD(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned long size = B_A_OP_CCCC( b, v, vdesc );

    vdesc->push_back( OPVALUE );
    for(int i=1; i < v->size(); i++)
        vdesc->push_back( REGISTER );

    (*vdesc)[3] = FIELD;

    return size;
}

unsigned long B_A_OP_CCCC_3_TYPE(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned long size = B_A_OP_CCCC( b, v, vdesc );

    vdesc->push_back( OPVALUE );
    for(int i=1; i < v->size(); i++)
        vdesc->push_back( REGISTER );

    (*vdesc)[3] = TYPE;

    return size;
}

unsigned long B_A_OP_CCCC_G_F_E_D(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    //memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    //memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)i16 );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    //memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xf) );

    v->push_back( (unsigned long)((i16 >> 4) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    return 6;
}

unsigned long OP_00(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned char i8;

    i8 = *( reinterpret_cast<unsigned char *>( const_cast<char *>(b->read(1))) );
    v->push_back( (unsigned long)(i8) );

    b->read(1);

    vdesc->push_back( OPVALUE );

    return 2;
}

unsigned long AA_OP_SBBBB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    signed short si16;
    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );

    return 4;
}

unsigned long SB_A_OP(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    signed short si16;

    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16 & 0xff) );
    v->push_back( (unsigned long)((si16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((si16 >> 12) & 0xf) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );

    return 2;
}

unsigned long AA_OP(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    
    return 2;
}

unsigned long AA_OP_BBBB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16) );

    vdesc->push_back( OPVALUE );
    for(int i=1; i < v->size(); i++)
        vdesc->push_back( REGISTER );

    return 4;
}

unsigned long AA_OP_BBBB_2_FIELD(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned long size = AA_OP_BBBB( b, v, vdesc );

    (*vdesc)[2] = FIELD;

    return size;
}

unsigned long AA_OP_BBBB_2_TYPE(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned long size = AA_OP_BBBB( b, v, vdesc );

    (*vdesc)[2] = TYPE;
    
    return size;
}

unsigned long AA_OP_BBBB_2_STRING(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned long size = AA_OP_BBBB( b, v, vdesc );

    (*vdesc)[2] = STRING;
    
    return size;
}

unsigned long OP_SAA(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned char i8;
    signed char si8;

    i8 = *( reinterpret_cast<unsigned char *>( const_cast<char *>(b->read(1))) );
    v->push_back( (unsigned long)(i8) );

    si8 = *( reinterpret_cast<signed char *>( const_cast<char *>(b->read(1))) );
    v->push_back( (unsigned long)(si8) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( INTEGER );
    
    return 2;
}

unsigned long B_A_OP(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( REGISTER );

    return 2;
}

unsigned long _00_OP_SAAAA(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    signed short si16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );

    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( INTEGER );
    
    return 4;
}

unsigned long B_A_OP_SCCCC(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    signed short si16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );


    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)si16 );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );
    
    return 4;
}

unsigned long AA_OP_CC_BB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( REGISTER );
    vdesc->push_back( REGISTER );

    return 4;
}

unsigned long AA_OP_BB_SCC(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    unsigned char i8;
    char si8;

    v->push_back( 4 );
    
    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    i8 = *( reinterpret_cast<unsigned char *>( const_cast<char *>(b->read(1))) );
    v->push_back( (unsigned long)(i8) );

    si8 = *( reinterpret_cast<signed char *>( const_cast<char *>(b->read(1))) );
    v->push_back( (unsigned long)(si8) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );

    return 4;
}

unsigned long AA_OP_SBBBBBBBB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    signed int si32;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    si32 = *( reinterpret_cast<signed int *>( const_cast<char *>(b->read(4))) );
    v->push_back( (unsigned long)(si32) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );
    
    return 6;
}

unsigned long AA_OP_BBBB_CCCC(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16) );

    return 6;
}

unsigned long AA_OP_SBBBB_SBBBB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    signed short si16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );
   
    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );
    vdesc->push_back( INTEGER );
    
    return 6;
}

unsigned long AA_OP_SBBBB_SBBBB_SBBBB_SBBBB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;
    signed short si16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );
    
    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );

    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );

    si16 = *( reinterpret_cast<signed short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(si16) );

    vdesc->push_back( OPVALUE );
    vdesc->push_back( REGISTER );
    vdesc->push_back( INTEGER );
    vdesc->push_back( INTEGER );
    vdesc->push_back( INTEGER );
    vdesc->push_back( INTEGER );

    return 10;
}

unsigned long _00_OP_AAAA_BBBB(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc) {
    unsigned short i16;

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16 & 0xff) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16) );

    i16 = *( reinterpret_cast<unsigned short *>( const_cast<char *>(b->read(2))) );
    v->push_back( (unsigned long)(i16) );

    return 6;
}

void INVOKE(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc, vector<unsigned long> *d, unsigned long *min_data) {
    unsigned long nb_arg = (*v)[2];
    unsigned long meth = (*v)[3];
    vector<unsigned long>::iterator it;

    /*
    printf("NB = %d %d\n", nb_arg, meth);
    for(int ii=0; ii < v->size(); ii++) {
        printf("%d ", (*v)[ii]);
    }                    
    printf("\n");
    */

    if (nb_arg == 5) {
        unsigned long op_1 = (*v)[1];
        //operands = [operands[ 0 ]] + operands[ 4 : 4 + operands[ 2 ][1] ] + [operands[ 1 ]] + [operands[ 3 ]]
        it=v->begin()+4;
        v->insert( v->begin()+1, it, it+4+nb_arg );
        v->erase( v->begin()+nb_arg, v->end() );

        v->push_back( op_1 );
        v->push_back( meth );
/*
        printf("OP1 = %d\n", op_1);
        for(int ii=0; ii < v->size(); ii++) {
            printf("%d ", (*v)[ii]);
        }                    
        printf("\n");
        
        exit(0);
*/
    }
    else {
        // operands = [operands[ 0 ]] + operands[ 4 : 4 + operands[ 2 ][1] ] + [operands[ 3 ]];
        it=v->begin()+4;
        v->insert( v->begin()+1, it, it+4+nb_arg ); 
        v->erase( v->begin()+nb_arg+1, v->end() );
    
        v->push_back( meth );
    }


    vdesc->push_back( OPVALUE );
    for(int i=1; i < v->size(); i++)
        vdesc->push_back( REGISTER );

    (*vdesc)[ vdesc->size() - 1 ] = METHOD;
}

void INVOKERANGE(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc, vector<unsigned long> *d, unsigned long *min_data) {
    unsigned long nb_arg = (*v)[1];
    unsigned long meth = (*v)[2];
    vector<unsigned long>::iterator it;

    unsigned long NNNN = (*v)[3] + (*v)[1] + 1;

    for(int ii = (*v)[3]+1; ii < NNNN - 1; ii++) {
        v->push_back( ii );
    }

    v->push_back( meth );
    v->erase( v->begin()+1, v->begin()+3 );

    vdesc->push_back( OPVALUE );
    for(int i=1; i < v->size(); i++)
        vdesc->push_back( REGISTER );

    (*vdesc)[ vdesc->size() - 1 ] = METHOD;
}

typedef struct fillarraydata {
    unsigned short ident;
    unsigned short element_width;
    unsigned long size;
} fillarraydata_t;

void FILLARRAYDATA(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc, vector<unsigned long> *d, unsigned long *min_data) {
    unsigned long value = ((*v)[2] * 2) + b->get_current_idx() - 6;

//    printf("MIN_DATA = %d %d %d %d %d\n", b->get_end(), b->get_current_idx(), *min_data, (*v)[3], value);
    if (*min_data > value) {
        *min_data = value;
    }

    d->push_back( 0 );
    d->push_back( value );
}

typedef struct sparseswitch {
    unsigned short ident;
    unsigned short size;
} sparseswitch_t;

void SPARSESWITCH(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc, vector<unsigned long> *d, unsigned long *min_data) {
//    printf("SPARSESWITCH\n"); fflush(stdout);

    unsigned long value = ((*v)[2] * 2) + b->get_current_idx() - 6;

    if (*min_data > value) {
        *min_data = value;
    }

    d->push_back( 1 );
    d->push_back( value );
}

typedef struct packedswitch {
    unsigned short ident;
    unsigned short size;
    unsigned long first_key;
} packedswitch_t;

void PACKEDSWITCH(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc, vector<unsigned long> *d, unsigned long *min_data) {
//    printf("PACKEDSWITCH\n"); fflush(stdout);

    unsigned long value = ((*v)[2] * 2) + b->get_current_idx() - 6;

    //printf("MIN_DATA = %d %d %d %d %d\n", b->get_end(), b->get_current_idx(), *min_data, (*v)[2], value);
    if (*min_data > value) {
        *min_data = value;
    }

    d->push_back( 2 );
    d->push_back( value );
}


void DEFAULT(Buff *b, vector<unsigned long> *v, vector<unsigned long> *vdesc, vector<unsigned long> *d, unsigned long *min_data) {

}

typedef struct LOperands {
    unsigned long value;
    struct LOperands *next;
} LOperands_t;

class DBC {
    public :
        unsigned char op_value;
        size_t op_length;
        vector<unsigned long> *voperands;
        LOperands_t *lo;

    public :
        DBC(unsigned char value, vector<unsigned long> *v, size_t length) {
            op_value = value;
            voperands = v;
            op_length = length;
            lo = NULL;
        }

        int get_opvalue() {
            return op_value;
        }

        LOperands_t *get_operands() {
            if (voperands->size() == 1) {
                return NULL;
            }

            if (lo != NULL) {
                return lo;
            }

            LOperands_t *lo = (LOperands_t *)malloc( sizeof(LOperands_t) );
            LOperands_t *nlo;

            nlo = lo;
            for(int ii=1; ii < voperands->size(); ii++) {
                nlo->value = (*voperands)[ii];
                
                if (ii+1 == voperands->size())
                    break;

                nlo->next = (LOperands_t *)malloc( sizeof(LOperands_t) );
                nlo = nlo->next;
            }

            
            nlo->next = NULL;
            return lo;
        }

        size_t get_length() {
            return op_length;
        }
};

class DBCSpe {

    
};

class DCode {
    public :
        vector<DBC *> bytecodes;
        vector<DBCSpe *> bytecodes_spe;

    public :
        DCode() {

        }

        DCode(sparse_hash_map<int, unsigned long(*)(Buff *, vector<unsigned long>*, vector<unsigned long>*)> *parsebytecodes, 
              sparse_hash_map<int, void (*)(Buff *, vector<unsigned long> *, vector<unsigned long> *, vector<unsigned long> *, unsigned long *)> *postbytecodes, 
              Buff *b) {
            unsigned char op_value;
            unsigned long size;

            vector<unsigned long> *v;
            vector<unsigned long> *datas;
            unsigned long min_data = b->get_end();

            datas = new vector<unsigned long>;

            while (b->empty() == false) {
                op_value = *( reinterpret_cast<unsigned char *>( const_cast<char *>(b->read_false(1))) );

                vector<unsigned long> *v = new vector<unsigned long>;
                vector<unsigned long> *vdesc = new vector<unsigned long>;
                size = (*parsebytecodes)[ op_value ]( b, v, vdesc );

                if (op_value != (*v)[0]) { }

                /*
                if (postbytecodes->count( op_value ) == 0) {
                    DEFAULT( b, v );
                } else {
                    (*postbytecodes)[ op_value ]( b, v, datas, &min_data );
                }*/
                
                if (op_value == 0x26) {
                    (*postbytecodes)[ op_value ]( b, v, vdesc, datas, &min_data );
                } else if (op_value >= 0x2b && op_value <= 0x2c) {
                    (*postbytecodes)[ op_value ]( b, v, vdesc, datas, &min_data );
                } else if (op_value >= 0x6e && op_value <= 0x72) {
                    (*postbytecodes)[ op_value ]( b, v, vdesc, datas, &min_data );
                } else if ((op_value >= 0x74 && op_value <= 0x78) || op_value == 0x25) {
                    (*postbytecodes)[ op_value ]( b, v, vdesc, datas, &min_data );
                }

                /*
                if (postbytecodes->count( op_value ) == 0) {
                    DEFAULT( b, v, datas, &min_data );
                } 
                */

                /*
                for(int ii=0; ii < v->size(); ii++) {
                    printf("%d ", (*v)[ii]);
                }                    
                printf("\n");

                printf("END %d\n", b->get_current_idx());
                */

                bytecodes.push_back( new DBC(op_value, v, size) );
                
                /*printf("OP_VALUE %x ---> ", op_value); fflush(stdout);
                for(int ii=0; ii < v->size(); ii++) {
                    printf("%d ", (*v)[ii]);
                }                    
                printf(" : "); 
                for(int ii=0; ii < vdesc->size(); ii++) {
                    printf("%d ", (*vdesc)[ii]);
                }                    
                printf("\n");
                */

                if (vdesc->size() == 0) { exit(0); };

                if (b->get_current_idx() >= min_data) {
                    break;
                }
            }


            if (b->empty() == false) {
                //printf("LAAAAA\n");
                //cout << "la" << b->get_end() << " " << b->get_current_idx() << "\n";

                for(int ii=0; ii < datas->size(); ii+=2) {
                //printf("SPECIFIC %d %d\n", (*datas)[ii], (*datas)[ii+1]);

                    if ((*datas)[ii] == 0) {
                        fillarraydata_t fadt;

                        memcpy( &fadt, b->readat( (*datas)[ii+1], sizeof(fillarraydata_t) ), sizeof(fillarraydata_t) );
                        //printf("%d %d %d\n", fadt.ident, fadt.element_width, fadt.size);
                        //FILL_ARRAY_DATA_NAMEDTUPLE = namedtuple("FILL_ARRAY_DATA_NAMEDTUPLE", "ident element_width size")
                        //FILL_ARRAY_DATA = [ '=HHL', FILL_ARRAY_DATA_NAMEDTUPLE ]

                        b->readat( (*datas)[ii+1] + sizeof(fillarraydata_t), fadt.size * fadt.element_width ); 
                    } else if ((*datas)[ii] == 1) {
                        sparseswitch_t sst;

                        memcpy( &sst, b->readat( (*datas)[ii+1], sizeof(sparseswitch_t) ), sizeof(sparseswitch_t) );

                        b->readat( (*datas)[ii+1] + sizeof(sparseswitch_t), sst.size * 4 * 2 );
                    } else if ((*datas)[ii] == 2) {
                        packedswitch_t pst;

                        memcpy( &pst, b->readat( (*datas)[ii+1], sizeof(packedswitch_t) ), sizeof(packedswitch_t) );
                        
                        b->readat( (*datas)[ii+1] + sizeof(packedswitch_t), pst.size * 4 );
                    } else {
                        printf("OOOOPS\n"); fflush(stdout);
                        exit(0);
                    }
                }                    
                //printf("\n");
                //cout << "la" << b->get_end() << " " << b->get_current_idx() << "\n";
            }
        }

        int size() {
            return bytecodes.size() + bytecodes_spe.size();
        }

        DBC *get_bytecode_at(int i) {
            return bytecodes[ i ];
        }

        void get_code(sparse_hash_map<int, unsigned long(*)(Buff *, vector<unsigned long>*, vector<unsigned long>*)> *parsebytecodes,
                      Buff *b, unsigned long *values, size_t *values_len) {
            //op_value = unpack( '=B', self.__insn[j] )[0]
            /*
            unsigned char op_value;
            memcpy( &op_value, b->read_false( 1 ), 1 );

            //printf("OP_VALUE %x ---> ", op_value); fflush(stdout);

            vector<unsigned long> *v = (*bytecodes)[ op_value ]( b );

            for(int ii=0; ii < v->size(); ii++) {
                //printf("%d ", (*v)[ii]);
                values[ ii ] = (*v)[ii];
            }

            //printf("\n");
            *values_len = v->size();*/
        }
};

class DVM {
    public :
        debug_t dt;
        sparse_hash_map<int, unsigned long(*)(Buff *, vector<unsigned long>*, vector<unsigned long>*)> bytecodes;
        sparse_hash_map<int, void (*)(Buff *, vector<unsigned long> *, vector<unsigned long> *, vector<unsigned long> *, unsigned long *)> postbytecodes; 
        
        DCode d;
        Buff b;
    public :
        DVM() {
            bytecodes[ 0x0 ] = &OP_00;

            bytecodes[ 0x1 ] = &B_A_OP;

            bytecodes[ 0x2 ] = &AA_OP_BBBB;
            
            bytecodes[ 0x3 ] = &_00_OP_AAAA_BBBB;

            bytecodes[ 0x4 ] = &B_A_OP;
            bytecodes[ 0x5 ] = &AA_OP_BBBB;
            
            bytecodes[ 0x6 ] = &_00_OP_AAAA_BBBB;
            
            bytecodes[ 0x7 ] = &B_A_OP;
            bytecodes[ 0x8 ] = &AA_OP_BBBB;

            bytecodes[ 0xa ] = &AA_OP;
            bytecodes[ 0xb ] = &AA_OP;
            bytecodes[ 0xc ] = &AA_OP;
            bytecodes[ 0xd ] = &AA_OP;
            
            bytecodes[ 0xe ] = &OP_00;
            
            bytecodes[ 0xf ] = &AA_OP;
            
            bytecodes[ 0x10 ] = &AA_OP;
            bytecodes[ 0x11 ] = &AA_OP;
            bytecodes[ 0x12 ] = &SB_A_OP;

            bytecodes[ 0x13 ] = &AA_OP_SBBBB;
            bytecodes[ 0x14 ] = &AA_OP_SBBBB_SBBBB;
            bytecodes[ 0x15 ] = &AA_OP_SBBBB;
            bytecodes[ 0x16 ] = &AA_OP_SBBBB;
            
            bytecodes[ 0x17 ] = &AA_OP_SBBBB_SBBBB;
            bytecodes[ 0x18 ] = &AA_OP_SBBBB_SBBBB_SBBBB_SBBBB;

            bytecodes[ 0x19 ] = &AA_OP_SBBBB;
            
            bytecodes[ 0x1a ] = &AA_OP_BBBB_2_STRING;
            bytecodes[ 0x1c ] = &AA_OP_BBBB;
            
            bytecodes[ 0x1d ] = &AA_OP;
            bytecodes[ 0x1e ] = &AA_OP;
            
            bytecodes[ 0x1f ] = &AA_OP_BBBB;

            bytecodes[ 0x20 ] = &B_A_OP_CCCC_3_TYPE;
            bytecodes[ 0x21 ] = &B_A_OP;
            bytecodes[ 0x22 ] = &AA_OP_BBBB_2_TYPE;

            bytecodes[ 0x23 ] = &B_A_OP_CCCC_3_TYPE;
          
            bytecodes[ 0x26 ] = &AA_OP_SBBBBBBBB; postbytecodes[ 0x26 ] = &FILLARRAYDATA;

            bytecodes[ 0x27 ] = &B_A_OP;
            bytecodes[ 0x28 ] = &OP_SAA;
            
            bytecodes[ 0x29 ] = &_00_OP_SAAAA;

            bytecodes[ 0x2b ] = &AA_OP_SBBBBBBBB; postbytecodes[ 0x2b ] = &PACKEDSWITCH;
            bytecodes[ 0x2c ] = &AA_OP_SBBBBBBBB; postbytecodes[ 0x2c ] = &SPARSESWITCH;

            bytecodes[ 0x2d ] = &AA_OP_CC_BB;
            bytecodes[ 0x2e ] = &AA_OP_CC_BB;
            bytecodes[ 0x2f ] = &AA_OP_CC_BB;
            bytecodes[ 0x30 ] = &AA_OP_CC_BB;
            bytecodes[ 0x31 ] = &AA_OP_CC_BB;

            bytecodes[ 0x32 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0x33 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0x34 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0x35 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0x36 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0x37 ] = &B_A_OP_SCCCC;  

            bytecodes[ 0x38 ] = &AA_OP_SBBBB;
            bytecodes[ 0x39 ] = &AA_OP_SBBBB;
            bytecodes[ 0x3a ] = &AA_OP_SBBBB;
            bytecodes[ 0x3b ] = &AA_OP_SBBBB;
            bytecodes[ 0x3c ] = &AA_OP_SBBBB;
            bytecodes[ 0x3d ] = &AA_OP_SBBBB;

            bytecodes[ 0x40 ] = &OP_00;
            
            bytecodes[ 0x44 ] = &AA_OP_CC_BB;
            bytecodes[ 0x45 ] = &AA_OP_CC_BB;
            bytecodes[ 0x46 ] = &AA_OP_CC_BB;
            bytecodes[ 0x47 ] = &AA_OP_CC_BB;
            bytecodes[ 0x48 ] = &AA_OP_CC_BB;
            bytecodes[ 0x49 ] = &AA_OP_CC_BB;
            bytecodes[ 0x4a ] = &AA_OP_CC_BB;
            bytecodes[ 0x4b ] = &AA_OP_CC_BB;
            bytecodes[ 0x4c ] = &AA_OP_CC_BB;
            bytecodes[ 0x4d ] = &AA_OP_CC_BB;
            bytecodes[ 0x4e ] = &AA_OP_CC_BB;
            bytecodes[ 0x4f ] = &AA_OP_CC_BB;
            bytecodes[ 0x50 ] = &AA_OP_CC_BB;
            bytecodes[ 0x51 ] = &AA_OP_CC_BB;

            bytecodes[ 0x52 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x53 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x54 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x55 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x56 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x57 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x58 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x59 ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x5a ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x5b ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x5c ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x5d ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x5e ] = &B_A_OP_CCCC_3_FIELD;
            bytecodes[ 0x5f ] = &B_A_OP_CCCC_3_FIELD;
            
            bytecodes[ 0x60 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x61 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x62 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x63 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x64 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x65 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x66 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x67 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x68 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x69 ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x6a ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x6b ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x6c ] = &AA_OP_BBBB_2_FIELD;
            bytecodes[ 0x6d ] = &AA_OP_BBBB_2_FIELD;

            bytecodes[ 0x6e ] = &B_A_OP_CCCC_G_F_E_D; postbytecodes[ 0x6e ] = &INVOKE;
            bytecodes[ 0x6f ] = &B_A_OP_CCCC_G_F_E_D; postbytecodes[ 0x6f ] = &INVOKE;
            bytecodes[ 0x70 ] = &B_A_OP_CCCC_G_F_E_D; postbytecodes[ 0x70 ] = &INVOKE;
            bytecodes[ 0x71 ] = &B_A_OP_CCCC_G_F_E_D; postbytecodes[ 0x71 ] = &INVOKE;
            bytecodes[ 0x72 ] = &B_A_OP_CCCC_G_F_E_D; postbytecodes[ 0x72 ] = &INVOKE;
       
            bytecodes[ 0x73 ] = &OP_00;
            
            bytecodes[ 0x74 ] = &AA_OP_BBBB_CCCC; postbytecodes[ 0x74 ] = &INVOKERANGE;
            bytecodes[ 0x75 ] = &AA_OP_BBBB_CCCC; postbytecodes[ 0x75 ] = &INVOKERANGE;
            bytecodes[ 0x76 ] = &AA_OP_BBBB_CCCC; postbytecodes[ 0x76 ] = &INVOKERANGE;
            bytecodes[ 0x77 ] = &AA_OP_BBBB_CCCC; postbytecodes[ 0x77 ] = &INVOKERANGE;
            bytecodes[ 0x78 ] = &AA_OP_BBBB_CCCC; postbytecodes[ 0x78 ] = &INVOKERANGE;

            bytecodes[ 0x7b ] = &B_A_OP;
            bytecodes[ 0x7c ] = &B_A_OP;
            bytecodes[ 0x7d ] = &B_A_OP;
            bytecodes[ 0x7e ] = &B_A_OP;
            bytecodes[ 0x7f ] = &B_A_OP;
            bytecodes[ 0x80 ] = &B_A_OP;
            bytecodes[ 0x81 ] = &B_A_OP;
            bytecodes[ 0x82 ] = &B_A_OP;
            bytecodes[ 0x83 ] = &B_A_OP;
            bytecodes[ 0x84 ] = &B_A_OP;
            bytecodes[ 0x85 ] = &B_A_OP;
            bytecodes[ 0x86 ] = &B_A_OP;
            bytecodes[ 0x87 ] = &B_A_OP;
            bytecodes[ 0x88 ] = &B_A_OP;
            bytecodes[ 0x89 ] = &B_A_OP;
            bytecodes[ 0x8a ] = &B_A_OP;
            bytecodes[ 0x8b ] = &B_A_OP;
            bytecodes[ 0x8c ] = &B_A_OP;
            bytecodes[ 0x8d ] = &B_A_OP;
            bytecodes[ 0x8e ] = &B_A_OP;
            bytecodes[ 0x8f ] = &B_A_OP;
            
            bytecodes[ 0x90 ] = &AA_OP_CC_BB;
            bytecodes[ 0x91 ] = &AA_OP_CC_BB;
            bytecodes[ 0x92 ] = &AA_OP_CC_BB;
            bytecodes[ 0x93 ] = &AA_OP_CC_BB;
            bytecodes[ 0x94 ] = &AA_OP_CC_BB;
            bytecodes[ 0x95 ] = &AA_OP_CC_BB;
            bytecodes[ 0x96 ] = &AA_OP_CC_BB;
            bytecodes[ 0x97 ] = &AA_OP_CC_BB;
            bytecodes[ 0x98 ] = &AA_OP_CC_BB;
            bytecodes[ 0x99 ] = &AA_OP_CC_BB;
            bytecodes[ 0x9a ] = &AA_OP_CC_BB;
            bytecodes[ 0x9b ] = &AA_OP_CC_BB;
            bytecodes[ 0x9c ] = &AA_OP_CC_BB;
            bytecodes[ 0x9d ] = &AA_OP_CC_BB;
            bytecodes[ 0x9e ] = &AA_OP_CC_BB;
            bytecodes[ 0x9f ] = &AA_OP_CC_BB;
            bytecodes[ 0xa0 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa1 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa2 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa3 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa4 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa5 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa6 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa7 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa8 ] = &AA_OP_CC_BB;
            bytecodes[ 0xa9 ] = &AA_OP_CC_BB;
            bytecodes[ 0xaa ] = &AA_OP_CC_BB;
            bytecodes[ 0xab ] = &AA_OP_CC_BB;
            bytecodes[ 0xac ] = &AA_OP_CC_BB;
            bytecodes[ 0xad ] = &AA_OP_CC_BB;
            bytecodes[ 0xae ] = &AA_OP_CC_BB;
            bytecodes[ 0xaf ] = &AA_OP_CC_BB;
            
            bytecodes[ 0xb0 ] = &B_A_OP;
            bytecodes[ 0xb1 ] = &B_A_OP;
            bytecodes[ 0xb2 ] = &B_A_OP;
            bytecodes[ 0xb3 ] = &B_A_OP;
            bytecodes[ 0xb4 ] = &B_A_OP;
            bytecodes[ 0xb5 ] = &B_A_OP;
            bytecodes[ 0xb6 ] = &B_A_OP;
            bytecodes[ 0xb7 ] = &B_A_OP;
            bytecodes[ 0xb8 ] = &B_A_OP;
            bytecodes[ 0xb9 ] = &B_A_OP;
            bytecodes[ 0xba ] = &B_A_OP;
            bytecodes[ 0xbb ] = &B_A_OP;
            bytecodes[ 0xbc ] = &B_A_OP;
            bytecodes[ 0xbd ] = &B_A_OP;
            bytecodes[ 0xbe ] = &B_A_OP;
            bytecodes[ 0xbf ] = &B_A_OP;
            bytecodes[ 0xc0 ] = &B_A_OP;
            bytecodes[ 0xc1 ] = &B_A_OP;
            bytecodes[ 0xc2 ] = &B_A_OP;
            bytecodes[ 0xc3 ] = &B_A_OP;
            bytecodes[ 0xc4 ] = &B_A_OP;
            bytecodes[ 0xc5 ] = &B_A_OP;
            bytecodes[ 0xc6 ] = &B_A_OP;
            bytecodes[ 0xc7 ] = &B_A_OP;
            bytecodes[ 0xc8 ] = &B_A_OP;
            bytecodes[ 0xc9 ] = &B_A_OP;
            bytecodes[ 0xca ] = &B_A_OP;
            bytecodes[ 0xcb ] = &B_A_OP;
            bytecodes[ 0xcc ] = &B_A_OP;
            bytecodes[ 0xcd ] = &B_A_OP;
            bytecodes[ 0xce ] = &B_A_OP;
            bytecodes[ 0xcf ] = &B_A_OP;

            bytecodes[ 0xd0 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd1 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd2 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd3 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd4 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd5 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd6 ] = &B_A_OP_SCCCC;  
            bytecodes[ 0xd7 ] = &B_A_OP_SCCCC;  
            
            bytecodes[ 0xd8 ] = &AA_OP_BB_SCC;
            bytecodes[ 0xd9 ] = &AA_OP_BB_SCC;
            bytecodes[ 0xda ] = &AA_OP_BB_SCC;
            bytecodes[ 0xdb ] = &AA_OP_BB_SCC;
            bytecodes[ 0xdc ] = &AA_OP_BB_SCC;
            bytecodes[ 0xdd ] = &AA_OP_BB_SCC;
            bytecodes[ 0xde ] = &AA_OP_BB_SCC;
            bytecodes[ 0xdf ] = &AA_OP_BB_SCC;
            bytecodes[ 0xe0 ] = &AA_OP_BB_SCC;
            bytecodes[ 0xe1 ] = &AA_OP_BB_SCC;
            bytecodes[ 0xe2 ] = &AA_OP_BB_SCC;

            bytecodes[ 0xe8 ] = &OP_00;

        }

        int add(const char *data, size_t data_len) {
            Buff b = Buff( data, data_len );
            
            Header h = Header( &b );
            MapList m = MapList( &b );

            return 0;   
        }

        DCode *new_code(const char *data, size_t data_len) {
            Buff b = Buff( data, data_len );
            DCode *d = new DCode( &bytecodes, &postbytecodes, &b );

            return d;
        }
};

extern "C" DVM *init() {
    return new DVM();
}

extern "C" int add(DVM &d, const char *data, size_t data_len) {
   return d.add( data, data_len );
}

extern "C" DCode *new_code(DVM &d, const char *data, size_t data_len) {
   return d.new_code( data, data_len );
}


extern "C" int get_nb_bytecodes(DCode *d) {
    return d->size();
}

extern "C" DBC *get_bytecode_at(DCode *d, int i) {
    return d->get_bytecode_at( i );
}

extern "C" int get_opvalue(DBC *d) {
    return d->get_opvalue();
}

extern "C" int get_length(DBC *d) {
    return d->get_length();
}

extern "C" LOperands_t *get_operands(DBC *d) {
    return d->get_operands();
}

typedef struct {
    PyObject_HEAD;
    DVM *dparent;
    DCode *d;
} dvm_DCodeObject;

static void
DCode_dealloc(dvm_DCodeObject* self)
{
    cout<<"Called dcode dealloc\n";

    delete self->d;
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject *DCode_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    dvm_DCodeObject *self;

    self = (dvm_DCodeObject *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->d = NULL;
    }

    return (PyObject *)self;
}

static int
DCode_init(dvm_DCodeObject *self, PyObject *args, PyObject *kwds)
{
    const char *code;
    size_t code_len;

    if (self != NULL) {
        cout<<"Called dcode init\n"; 
        
        int ok = PyArg_ParseTuple( args, "s#", &code, &code_len);
        if(!ok) return -1;
    

        self->d = self->dparent->new_code( code, code_len );
    }

    return 0;
}

static PyObject *DCode_get_nb_bytecodes(dvm_DCodeObject *self, PyObject* args)
{
    cout<<"Called get_nb_bytecodes()\n"; 

    return Py_BuildValue("i", self->d->size());
}

static PyMethodDef DCode_methods[] = {
    {"get_nb_bytecodes",  (PyCFunction)DCode_get_nb_bytecodes, METH_NOARGS, "get nb bytecodes" },
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyTypeObject dvm_DCodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "dvm.DCode",             /*tp_name*/
    sizeof(dvm_DCodeObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)DCode_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "DCode objects",           /* tp_doc */
    0,                     /* tp_traverse */
    0,                     /* tp_clear */
    0,                     /* tp_richcompare */
    0,                     /* tp_weaklistoffset */
    0,                     /* tp_iter */
    0,                     /* tp_iternext */
    DCode_methods,             /* tp_methods */
    NULL, //Noddy_members,             /* tp_members */
    NULL, //Noddy_getseters,           /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)DCode_init,      /* tp_init */
    0,                         /* tp_alloc */
    DCode_new,                 /* tp_new */
};

typedef struct {
    PyObject_HEAD;
    DVM *d;
} dvm_DVMObject;

static void
DVM_dealloc(dvm_DVMObject* self)
{
    cout<<"Called dvm dealloc\n";
    delete self->d;
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject *DVM_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    dvm_DVMObject *self;

    self = (dvm_DVMObject *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->d = NULL;
    }

    return (PyObject *)self;
}

static int
DVM_init(dvm_DVMObject *self, PyObject *args, PyObject *kwds)
{
    if (self != NULL)
        self->d = new DVM();
    
    return 0;
}

static PyObject *DVM_new_code(dvm_DVMObject *self, PyObject* args)
{
    cout<<"Called new code()\n"; 

    PyObject *nc = DCode_new(&dvm_DCodeType, NULL, NULL);
 
    dvm_DCodeObject *dnc = (dvm_DCodeObject *)nc;

    dnc->dparent = self->d;
    DCode_init( (dvm_DCodeObject *)nc, args, NULL );
   
    Py_INCREF( nc );

    return nc;
}

static PyMethodDef DVM_methods[] = {
    {"new_code",  (PyCFunction)DVM_new_code, METH_VARARGS, "new code" },
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyTypeObject dvm_DVMType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "dvm.DVM",             /*tp_name*/
    sizeof(dvm_DVMObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)DVM_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "DVM objects",           /* tp_doc */
    0,                     /* tp_traverse */
    0,                     /* tp_clear */
    0,                     /* tp_richcompare */
    0,                     /* tp_weaklistoffset */
    0,                     /* tp_iter */
    0,                     /* tp_iternext */
    DVM_methods,             /* tp_methods */
    NULL, //Noddy_members,             /* tp_members */
    NULL, //Noddy_getseters,           /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)DVM_init,      /* tp_init */
    0,                         /* tp_alloc */
    DVM_new,                 /* tp_new */
};

static PyMethodDef dvm_methods[] = {
    {NULL}  /* Sentinel */
};

/*
static void PyDelDVM(void *ptr)
{
    cout<<"Called PyDelDVM()\n"; 
    DVM *d = static_cast<DVM *>(ptr);
    delete d;
    return;
}

static void PyDelDCode(void *ptr)
{
    cout<<"Called PyDelDCode()\n"; 
    DCode *d = static_cast<DCode *>(ptr);
    delete d;
    return;
}

PyObject *python_new_DVM(PyObject *, PyObject* args) {
    DVM *d = new DVM();

    return PyCObject_FromVoidPtr( d, PyDelDVM);
}

PyObject *python_new_code(PyObject *, PyObject* args)
{
    cout<<"Called new code()\n"; 
    PyObject *pydvm = NULL;
    const char *code;
    size_t code_len;

    int ok = PyArg_ParseTuple( args, "Os#", &pydvm, &code, &code_len);
    if(!ok) return NULL;

    void * temp = PyCObject_AsVoidPtr(pydvm);

    DVM *d = static_cast<DVM *>(temp);

    DCode *nc = d->new_code( code, code_len );

    return PyCObject_FromVoidPtr( nc, PyDelDCode );
}

static PyMethodDef DVMNativeMethods[] = {
    {"DVM",  python_new_DVM, METH_VARARGS, "Create new Dalvik Virtual Machine module." },
    {"new_code",  python_new_code, METH_VARARGS, "new code" },
    {NULL, NULL, 0, NULL}        
};*/

extern "C" PyMODINIT_FUNC initdvmnative(void) {
    PyObject *m;

    dvm_DVMType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&dvm_DVMType) < 0)
        return;

    dvm_DCodeType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&dvm_DCodeType) < 0)
        return;

    m = Py_InitModule3("dvmnative", dvm_methods, "Example module that creates an extension type.");

    Py_INCREF(&dvm_DVMType);
    PyModule_AddObject(m, "DVM", (PyObject *)&dvm_DVMType);
    
    Py_INCREF(&dvm_DCodeType);
    PyModule_AddObject(m, "DCode", (PyObject *)&dvm_DCodeType);
    
    //SpamError = PyErr_NewException("spam.error", NULL, NULL);
    //Py_INCREF(SpamError);
    //PyModule_AddObject(m, "error", SpamError);
}

#endif
