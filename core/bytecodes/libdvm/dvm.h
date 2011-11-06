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
#ifndef DVM_H
#define DVM_H

#include <Python.h>

#ifdef __cplusplus

#include <iostream>
#include <hash_map>
#include <string>
#include <vector>

#include "buff.h"

using namespace __gnu_cxx;
using namespace std;
using std::cout;
using std::endl;

typedef struct fillarraydata {
    unsigned short ident;
    unsigned short element_width;
    unsigned long size;
} fillarraydata_t;

typedef struct sparseswitch {
    unsigned short ident;
    unsigned short size;
} sparseswitch_t;

typedef struct packedswitch {
    unsigned short ident;
    unsigned short size;
    unsigned long first_key;
} packedswitch_t;

class DBC {
    public :
        unsigned char op_value;
        const char *op_name;
        size_t op_length;
        vector<unsigned long> *voperands;
        vector<unsigned long> *vdescoperands;

    public :
        DBC(unsigned char value, const char *name, vector<unsigned long> *v, vector<unsigned long> *vdesc, size_t length);
        ~DBC();
        int get_opvalue();
        const char *get_opname();
        size_t get_length();
};

class DBCSpe {  
    public :
        virtual const char *get_opname()=0;
        virtual size_t get_length()=0;
        virtual size_t get_type()=0;
};

class FillArrayData : public DBCSpe {
    public : 
        fillarraydata_t fadt;
        char *data;
        size_t data_size;
    public :
        FillArrayData(Buff *b, unsigned long off);
        ~FillArrayData();
        const char *get_opname();
        size_t get_length();
        size_t get_type();
};

class SparseSwitch : public DBCSpe {
    public : 
        sparseswitch_t sst;
        vector<int> keys;
        vector<int> targets;

    public :
        SparseSwitch(Buff *b, unsigned long off);
        ~SparseSwitch();
        const char *get_opname();
        size_t get_length();
        size_t get_type();
};

class PackedSwitch : public DBCSpe {
    public : 
        packedswitch_t pst;
        vector<int> targets;

    public :
        PackedSwitch(Buff *b, unsigned long off);
        ~PackedSwitch();
        const char *get_opname();
        size_t get_length();
        size_t get_type();
};

class DCode {
    public :
        vector<DBC *> bytecodes;
        vector<DBCSpe *> bytecodes_spe;

    public :
        DCode();
        ~DCode();
        DCode(vector<unsigned long(*)(Buff *, vector<unsigned long>*, vector<unsigned long>*)> *parsebytecodes,
              vector<void (*)(Buff *, vector<unsigned long> *, vector<unsigned long> *, vector<unsigned long> *, unsigned long *)> *postbytecodes,
              vector<const char *> *bytecodes_names,
              Buff *b);
        int size();
        DBC *get_bytecode_at(int i);
};

class DalvikBytecode {
    public :
        vector<unsigned long(*)(Buff *, vector<unsigned long>*, vector<unsigned long>*)> bytecodes;
        vector<void (*)(Buff *, vector<unsigned long> *, vector<unsigned long> *, vector<unsigned long> *, unsigned long *)> postbytecodes;

        vector<const char *> bytecodes_names;

    public :
        DalvikBytecode();
        DCode *new_code(const char *data, size_t data_len);
};

#endif
#endif
