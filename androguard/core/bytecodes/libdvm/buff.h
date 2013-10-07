/*
 This file is part of Androguard.

 Copyright (C) 2011, Anthony Desnos <desnos at t0t0.fr>
 All rights reserved.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS-IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
*/

#ifndef BUFF_H
#define BUFF_H

#ifdef __cplusplus

#if defined __GNUC__ || defined __APPLE__
#include <ext/hash_map>
#else
#include <hash_map>
#endif

#include <iostream>
#include <string>
#include <vector>

using namespace __gnu_cxx;
using namespace std;
using std::cout;
using std::endl;

class Buff {
    public :
        const char *bdata;
        size_t bdata_len;
        size_t bcurrent_idx;

        vector<unsigned int *> DynamicOffsets;
    public :
        Buff();
        Buff(const char *data, size_t data_len);
        Buff(const char *data, size_t data_len, size_t current_idx);
        void setup(const char *data, size_t data_len, size_t current_idx);
        const char *read(size_t len);
        const char *readat(size_t pos, size_t len);
        const char *read_false(size_t len);
        size_t get_current_idx();
        size_t get_end();
        bool empty();
        int register_dynamic_offset(unsigned int *addr);
        int set_idx(unsigned int);
        unsigned char read_uc();
        char read_c();
        unsigned long read_ul();
        unsigned int read_ui();
        unsigned short read_us();
};

#endif

#endif
