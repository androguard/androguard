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

#include "buff.h"

#include <stdio.h>

Buff::Buff() {

}

Buff::Buff(const char *data, size_t data_len) {
    bdata = data;
    bdata_len = data_len;
    bcurrent_idx = 0;
}

Buff:: Buff(const char *data, size_t data_len, size_t current_idx) {
    bdata = data;
    bdata_len = data_len;
    bcurrent_idx = current_idx;
}

void Buff::setup(const char *data, size_t data_len, size_t current_idx) {
    bdata = data;
    bdata_len = data_len;
    bcurrent_idx = current_idx;
}

const char *Buff::read(size_t len) {
    //cout << "read add " << bcurrent_idx << " " << len << "\n";
    bcurrent_idx += len;
    return (bdata + (bcurrent_idx - len));
}

const char *Buff::readat(size_t pos, size_t len) {
    return (bdata + (pos));
}

const char *Buff::read_false(size_t len) {
    return (bdata + (bcurrent_idx));
}

size_t Buff::get_current_idx() {
    return bcurrent_idx;
}

size_t Buff::get_end() {
    return bdata_len;
}

bool Buff::empty() {
    return bcurrent_idx == bdata_len;
}

int Buff::register_dynamic_offset(unsigned int *addr) {
    DynamicOffsets.push_back( addr );
}

int Buff::set_idx(unsigned int idx) {
    bcurrent_idx = idx;
}

unsigned char Buff::read_uc() {
    return *( reinterpret_cast<unsigned char *>( const_cast<char *>(this->read(1))) );
}

char Buff::read_c() {
    return *( reinterpret_cast<char *>( const_cast<char *>(this->read(1))) );
}

unsigned long Buff::read_ul() {
    return *( reinterpret_cast<unsigned long *>( const_cast<char *>(this->read(4))) );
}

unsigned int Buff::read_ui() {
    return *( reinterpret_cast<unsigned int *>( const_cast<char *>(this->read(4))) );
}

unsigned short Buff::read_us() {
    return *( reinterpret_cast<unsigned short *>( const_cast<char *>(this->read(2))) );
}
