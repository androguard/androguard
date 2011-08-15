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

// 0x5b : [ "22c", "iput-object",          "vA, vB, field@CCCC", [ OPCODE_B_A_OP, OPCODE_CCCC ], { 3 : "field@" } ],
// 0x5b : OPCODE_B_A_OP, OPCODE_CCCC 

//OPCODE_B_A_OP   :   op_B_A_OP,
//OPCODE_CCCC     :   op_CCCC,

/*
def op_B_A_OP(insn, current_pos) :
    i16 = unpack("=H", insn[current_pos:current_pos+2])[0]
    return [2, [i16 & 0xff, (i16 >> 8) & 0xf, (i16 >> 12) & 0xf]]
        
def op_CCCC(insn, current_pos) :
    i16 = unpack("=H", insn[current_pos:current_pos+2])[0]
    return [2, [i16]]
*/        

vector<unsigned long> *B_A_OP_CCCC(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;
    unsigned short *si16;

    v->push_back( 4 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)i16 );

    return v;
}

vector<unsigned long> *B_A_OP_CCCC_G_F_E_D(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 6 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)i16 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xf) );

    v->push_back( (unsigned long)((i16 >> 4) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    return v;
}

vector<unsigned long> *OP_00(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned char i8;

    v->push_back( 2 );
    
    memcpy( &i8, b->read( 1 ), 1 );
    v->push_back( (unsigned long)(i8) );

    b->read(1);

    return v;
}

vector<unsigned long> *AA_OP_SBBBB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 4 );
    
    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    signed short si16;
    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );

    return v;
}

vector<unsigned long> *SB_A_OP(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    signed short i16;

    v->push_back( 2 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    return v;
}

vector<unsigned long> *AA_OP(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 2 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    return v;
}

vector<unsigned long> *AA_OP_BBBB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 4 );
    
    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16) );

    return v;
}

vector<unsigned long> *OP_SAA(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned char i8;

    v->push_back( 2 );
    
    memcpy( &i8, b->read( 1 ), 1 );
    v->push_back( (unsigned long)(i8) );

    signed char si8;
    memcpy( &si8, b->read( 1 ), 1 );
    v->push_back( (unsigned long)(si8) );

    return v;
}

vector<unsigned long> *B_A_OP(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 2 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    return v;
}

vector<unsigned long> *_00_OP_SAAAA(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 4 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );

    signed short si16;
    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );

    return v;
}

vector<unsigned long> *B_A_OP_SCCCC(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 4 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xf) );
    v->push_back( (unsigned long)((i16 >> 12) & 0xf) );

    unsigned short si16;

    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)si16 );

    return v;
}

vector<unsigned long> *AA_OP_CC_BB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 4 );
    
    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    return v;
}

vector<unsigned long> *AA_OP_BB_SCC(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;
    unsigned char i8;
    char si8;

    v->push_back( 4 );
    
    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    memcpy( &i8, b->read( 1 ), 1 );
    v->push_back( (unsigned long)(i8) );

    memcpy( &si8, b->read( 1 ), 1 );
    v->push_back( (unsigned long)(si8) );

    return v;
}

vector<unsigned long> *AA_OP_SBBBBBBBB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;
    signed int i32;

    v->push_back( 6 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    memcpy( &i32, b->read( 4 ), 4 );
    v->push_back( (unsigned long)(i32) );

    return v;
}

vector<unsigned long> *AA_OP_BBBB_CCCC(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 6 );
    
    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16) );

    return v;
}

vector<unsigned long> *AA_OP_SBBBB_SBBBB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 6 );
    
    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    signed short si16;
    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );
    
    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );

    return v;
}

vector<unsigned long> *AA_OP_SBBBB_SBBBB_SBBBB_SBBBB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 10 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );
    v->push_back( (unsigned long)((i16 >> 8) & 0xff) );

    signed short si16;
    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );
    
    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );

    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );

    memcpy( &si16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(si16) );

    return v;
}

vector<unsigned long> *_00_OP_AAAA_BBBB(Buff *b) {
    vector<unsigned long> *v = new vector<unsigned long>;
    unsigned short i16;

    v->push_back( 6 );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16 & 0xff) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16) );

    memcpy( &i16, b->read( 2 ), 2 );
    v->push_back( (unsigned long)(i16) );

    return v;
}

void INVOKE(Buff *b, vector<unsigned long> *v, vector<unsigned long> *d, unsigned long *min_data) {
    unsigned long nb_arg = (*v)[2];
    unsigned long meth = (*v)[3];
    vector<unsigned long>::iterator it;

    //printf("NB = %d %d\n", nb_arg, meth);

    if (nb_arg == 5) {
        unsigned long op_1 = (*v)[1];
        //operands = [operands[ 0 ]] + operands[ 4 : 4 + operands[ 2 ][1] ] + [operands[ 1 ]] + [operands[ 3 ]]
        it=v->begin()+5;
        v->insert( v->begin()+1, it, it+5+nb_arg );
        v->erase( v->begin()+nb_arg+1, v->end() );

        v->push_back( op_1 );
        v->push_back( meth );
    }
    else {
        // operands = [operands[ 0 ]] + operands[ 4 : 4 + operands[ 2 ][1] ] + [operands[ 3 ]];
        it=v->begin()+5;
        v->insert( v->begin()+1, it, it+5+nb_arg ); 
        v->erase( v->begin()+nb_arg+1, v->end() );
    
        v->push_back( meth );
    }
}

typedef struct fillarraydata {
    unsigned short ident;
    unsigned short element_width;
    unsigned long size;
} fillarraydata_t;

void FILLARRAYDATA(Buff *b, vector<unsigned long> *v, vector<unsigned long> *d, unsigned long *min_data) {
    unsigned long value = (*v)[3] + b->get_current_idx();

    //printf("ADD %d %d\n", (*v)[3], value);

    if (*min_data > value) {
        *min_data = value;
    }

    d->push_back( value );
}


void DEFAULT(Buff *b, vector<unsigned long> *v, vector<unsigned long> *d, unsigned long *min_data) {

}

class DCode {
    public :
        DCode() {

        }

        DCode(sparse_hash_map<int, vector<unsigned long>*(*)(Buff *)> *bytecodes, 
              sparse_hash_map<int, void (*)(Buff *, vector<unsigned long> *, vector<unsigned long> *, unsigned long *)> *postbytecodes, 
              Buff *b) {
            unsigned char op_value;
            vector<unsigned long> *v;
            vector<unsigned long> *datas;
            unsigned long min_data = b->get_end();

            datas = new vector<unsigned long>;

            while (b->empty() == false) {
                memcpy( &op_value, b->read_false( 1 ), 1 );
            
                //printf("OP_VALUE %x ---> ", op_value); fflush(stdout);
                v = (*bytecodes)[ op_value ]( b );

                //for(int ii=0; ii < v->size(); ii++) {
                //    printf("%d ", (*v)[ii]);
                //}                    
                //printf("\n");

                //unsigned long size = (*v)[0];

                v->erase(v->begin(), v->begin()+1);

                if (op_value != (*v)[0]) { }

                if (op_value >= 0x6e && op_value <= 0x72) {
                }
                else if ((op_value >= 0x74 && op_value <= 0x78) || op_value == 0x25) {
                }

                if (postbytecodes->count( op_value ) == 0) {
                    DEFAULT( b, v, datas, &min_data );
                } else {
                    (*postbytecodes)[ op_value ]( b, v, datas, &min_data );
                }

                /*
                for(int ii=0; ii < v->size(); ii++) {
                    printf("%d ", (*v)[ii]);
                }                    
                printf("\n");

                printf("END %d\n", b->get_current_idx());
                */
                if (b->get_current_idx() >= min_data) {
                    break;
                }
            }

            if (b->empty() == false) {
                //printf("LAAAAA\n");
                //cout << "la" << b->get_end() << " " << b->get_current_idx() << "\n";

                for(int ii=0; ii < datas->size(); ii++) {
                    //printf("%d ", (*datas)[ii]);

                    fillarraydata_t fadt;

                    memcpy( &fadt, b->read( sizeof(fillarraydata_t) ), sizeof(fillarraydata_t) );
                    //printf("%d %d %d\n", fadt.ident, fadt.element_width, fadt.size);
                    //FILL_ARRAY_DATA_NAMEDTUPLE = namedtuple("FILL_ARRAY_DATA_NAMEDTUPLE", "ident element_width size")
                    //FILL_ARRAY_DATA = [ '=HHL', FILL_ARRAY_DATA_NAMEDTUPLE ]

                    b->read( fadt.size * fadt.element_width ); 
                }                    
                //printf("\n");

                //cout << "la" << b->get_end() << " " << b->get_current_idx() << "\n";
            }
        }

        void get_code(sparse_hash_map<int, vector<unsigned long>*(*)(Buff *)> *bytecodes, Buff *b, unsigned long *values, size_t *values_len) {
            //op_value = unpack( '=B', self.__insn[j] )[0]
            unsigned char op_value;
            memcpy( &op_value, b->read_false( 1 ), 1 );

            //printf("OP_VALUE %x ---> ", op_value); fflush(stdout);

            vector<unsigned long> *v = (*bytecodes)[ op_value ]( b );

            for(int ii=0; ii < v->size(); ii++) {
                //printf("%d ", (*v)[ii]);
                values[ ii ] = (*v)[ii];
            }

            //printf("\n");
            *values_len = v->size();
        }
};

class DVM {
    public :
        debug_t dt;
        sparse_hash_map<int, vector<unsigned long>*(*)(Buff *)> bytecodes;
        sparse_hash_map<int, void (*)(Buff *, vector<unsigned long> *, vector<unsigned long> *, unsigned long *)> postbytecodes; 
        
        
        unsigned long *exchange_buffer;
        size_t *len_exchange_buffer;
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
            
            bytecodes[ 0x1a ] = &AA_OP_BBBB;
            bytecodes[ 0x1c ] = &AA_OP_BBBB;
            
            bytecodes[ 0x1d ] = &AA_OP;
            bytecodes[ 0x1e ] = &AA_OP;
            
            bytecodes[ 0x1f ] = &AA_OP_BBBB;

            bytecodes[ 0x20 ] = &B_A_OP_CCCC;
            bytecodes[ 0x21 ] = &B_A_OP;
            bytecodes[ 0x22 ] = &AA_OP_BBBB;

            bytecodes[ 0x23 ] = &B_A_OP_CCCC;
          
            bytecodes[ 0x26 ] = &AA_OP_SBBBBBBBB; postbytecodes[ 0x26 ] = &FILLARRAYDATA;

            bytecodes[ 0x27 ] = &B_A_OP;
            bytecodes[ 0x28 ] = &OP_SAA;
            
            bytecodes[ 0x29 ] = &_00_OP_SAAAA;

            bytecodes[ 0x2b ] = &AA_OP_SBBBBBBBB;
            bytecodes[ 0x2c ] = &AA_OP_SBBBBBBBB;
            
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

            bytecodes[ 0x52 ] = &B_A_OP_CCCC;
            bytecodes[ 0x53 ] = &B_A_OP_CCCC;
            bytecodes[ 0x54 ] = &B_A_OP_CCCC;
            bytecodes[ 0x55 ] = &B_A_OP_CCCC;
            bytecodes[ 0x56 ] = &B_A_OP_CCCC;
            bytecodes[ 0x57 ] = &B_A_OP_CCCC;
            bytecodes[ 0x58 ] = &B_A_OP_CCCC;
            bytecodes[ 0x59 ] = &B_A_OP_CCCC;
            bytecodes[ 0x5a ] = &B_A_OP_CCCC;
            bytecodes[ 0x5b ] = &B_A_OP_CCCC;
            bytecodes[ 0x5c ] = &B_A_OP_CCCC;
            bytecodes[ 0x5d ] = &B_A_OP_CCCC;
            bytecodes[ 0x5e ] = &B_A_OP_CCCC;
            bytecodes[ 0x5f ] = &B_A_OP_CCCC;
            
            bytecodes[ 0x60 ] = &AA_OP_BBBB;
            bytecodes[ 0x61 ] = &AA_OP_BBBB;
            bytecodes[ 0x62 ] = &AA_OP_BBBB;
            bytecodes[ 0x63 ] = &AA_OP_BBBB;
            bytecodes[ 0x64 ] = &AA_OP_BBBB;
            bytecodes[ 0x65 ] = &AA_OP_BBBB;
            bytecodes[ 0x66 ] = &AA_OP_BBBB;
            bytecodes[ 0x67 ] = &AA_OP_BBBB;
            bytecodes[ 0x68 ] = &AA_OP_BBBB;
            bytecodes[ 0x69 ] = &AA_OP_BBBB;
            bytecodes[ 0x6a ] = &AA_OP_BBBB;
            bytecodes[ 0x6b ] = &AA_OP_BBBB;
            bytecodes[ 0x6c ] = &AA_OP_BBBB;
            bytecodes[ 0x6d ] = &AA_OP_BBBB;

            bytecodes[ 0x6e ] = &B_A_OP_CCCC_G_F_E_D;
            bytecodes[ 0x6f ] = &B_A_OP_CCCC_G_F_E_D;
            bytecodes[ 0x70 ] = &B_A_OP_CCCC_G_F_E_D; postbytecodes[ 0x70 ] = &INVOKE;
            bytecodes[ 0x71 ] = &B_A_OP_CCCC_G_F_E_D;
            bytecodes[ 0x72 ] = &B_A_OP_CCCC_G_F_E_D;
       
            bytecodes[ 0x73 ] = &OP_00;
            
            bytecodes[ 0x74 ] = &AA_OP_BBBB_CCCC;
            bytecodes[ 0x75 ] = &AA_OP_BBBB_CCCC;
            bytecodes[ 0x76 ] = &AA_OP_BBBB_CCCC;
            bytecodes[ 0x77 ] = &AA_OP_BBBB_CCCC;
            bytecodes[ 0x78 ] = &AA_OP_BBBB_CCCC;

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

        int setup_exchange_buffer(unsigned long *values, size_t *values_len) {
            exchange_buffer = values;
            len_exchange_buffer = values_len;

            return 0;
        }

        int add(const char *data, size_t data_len) {
            Buff b = Buff( data, data_len );
            
            Header h = Header( &b );
            MapList m = MapList( &b );

            return 0;   
        }

        int add_code(const char *data, size_t data_len, size_t current_pos) {
            //hexdump( (void *)data, data_len );


            b.setup( data, data_len, current_pos );
            d.get_code( &bytecodes, &b, exchange_buffer, len_exchange_buffer );
        }

        int new_code(const char *data, size_t data_len) {
            Buff b = Buff( data, data_len );
            DCode d = DCode( &bytecodes, &postbytecodes, &b );


        }
};

extern "C" DVM *init() {
    return new DVM();
}

extern "C" int add(DVM &d, const char *data, size_t data_len) {
   return d.add( data, data_len );
}

extern "C" int setup_exchange_buffer(DVM &d, unsigned long *values, size_t *values_len) {
    return d.setup_exchange_buffer( values, values_len );
}

extern "C" int add_code(DVM &d, const char *data, size_t data_len, size_t current_pos) {
   return d.add_code( data, data_len, current_pos );
}

extern "C" int new_code(DVM &d, const char *data, size_t data_len) {
   return d.new_code( data, data_len );
}

#endif
