#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

TYPE_DESCRIPTOR = {
    'V': 'void',
    'Z': 'boolean',
    'B': 'byte',
    'S': 'short',
    'C': 'char',
    'I': 'int',
    'J': 'long',
    'F': 'float',
    'D': 'double',
    'STR': 'String',
    'StringBuilder': 'String'
}

ACCESS_FLAGS_CLASSES = {
    0x1   : 'public',
    0x2   : 'private',
    0x4   : 'protected',
    0x8   : 'static',
    0x10  : 'final',
    0x200 : 'interface',
    0x400 : 'abstract',
    0x1000: 'synthetic',
    0x2000: 'annotation',
    0x4000: 'enum'
}

ACCESS_FLAGS_FIELDS = {
    0x1   : 'public',
    0x2   : 'private',
    0x4   : 'protected',
    0x8   : 'static',
    0x10  : 'final',
    0x40  : 'volatile',
    0x80  : 'transient',
    0x1000: 'synthetic',
    0x4000: 'enum'
}

ACCESS_FLAGS_METHODS = {
    0x1    : 'public',
    0x2    : 'private',
    0x4    : 'protected',
    0x8    : 'static',
    0x10   : 'final',
    0x20   : 'synchronized',
    0x40   : 'bridge',
    0x80   : 'varargs',
    0x100  : 'native',
    0x400  : 'abstract',
    0x800  : 'strict',
    0x1000 : 'synthetic',
    0x10000: '', # ACC_CONSTRUCTOR
    0x20000: 'synchronized'
}

TYPE_LEN = {
    'J': 2,
    'D': 2
}

DEBUG_MODES = {
    'off':  -1,
    'error': 0,
    'log':   1,
    'debug': 2
}

DEBUG_LEVEL = 'log'


class wrap_stream(object):
    def __init__(self):
        self.val = []
    def write(self, s):
        self.val.append(s)
    def clean(self):
        self.val = []
    def __str__(self):
        return ''.join(self.val)


def merge_inner(clsdict):
    '''
    Merge the inner class(es) of a class :
    e.g class A { ... } class A$foo{ ... } class A$bar{ ... }
       ==> class A { class foo{...} class bar{...} ... }
    '''
    samelist = False
    done = {}
    while not samelist:
        samelist = True
        classlist = clsdict.keys()
        for classname in classlist:
            parts_name = classname.split('$')
            if len(parts_name) > 2:
                parts_name = ['$'.join(parts_name[:-1]), parts_name[-1]]
            if len(parts_name) > 1:
                mainclass, innerclass = parts_name
                innerclass = innerclass[:-1] # remove ';' of the name
                mainclass += ';'
                if mainclass in clsdict:
                    clsdict[mainclass].add_subclass(innerclass, clsdict[classname])
                    clsdict[classname].name = innerclass
                    done[classname] = clsdict[classname]
                    del clsdict[classname]
                    samelist = False
                elif mainclass in done:
                    cls = done[mainclass]
                    cls.add_subclass(innerclass, clsdict[classname]) 
                    clsdict[classname].name = innerclass
                    done[classname] = done[mainclass]
                    del clsdict[classname]
                    samelist = False


def get_type_size(param):
    '''
    Return the number of register needed by the type @param
    '''
    return TYPE_LEN.get(param, 1)


def get_type(atype, size=None):
    '''
    Retrieve the type of a descriptor (e.g : I)
    '''
    if atype.startswith('java.lang'):
        atype = atype.replace('java.lang.', '')
    res = TYPE_DESCRIPTOR.get(atype.lstrip('java.lang'))
    if res is None:
        if atype[0] == 'L':
            res = atype[1:-1].replace('/', '.')
        elif atype[0] == '[':
            if size is None:
                res = '%s[]' % get_type(atype[1:])
            else:
                res = '%s[%s]' % (get_type(atype[1:]), size)
        else:
            res = atype
            log('Unknown descriptor: "%s".' % atype, 'debug')
    return res


def get_params_type(descriptor):
    '''
    Return the parameters type of a descriptor (e.g (IC)V)
    '''
    params = descriptor.split(')')[0][1:].split()
    if params:
        return [param for param in params]
    return []


def log(s, mode):
    def _log(s):
        print '%s' % s
    def _log_debug(s):
        print 'DEBUG: %s' % s
    def _log_error(s):
        print 'ERROR: %s' % s
        exit()
    if mode is None:
        return
    mode = DEBUG_MODES.get(mode)
    if mode <= DEBUG_MODES[DEBUG_LEVEL]:
        if mode == DEBUG_MODES['log']:
            _log(s)
        elif mode == DEBUG_MODES['debug']:
            _log_debug(s)
        elif mode == DEBUG_MODES['error']:
            _log_error(s)
