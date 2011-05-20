from itertools import count

TYPE_DESCRIPTOR = {
    'V': 'void',
    'Z': 'boolean',
    'B': 'byte',
    'S': 'short',
    'C': 'char',
    'I': 'int',
    'J': 'long',
    'F': 'float',
    'D': 'double'
}

ACCESS_FLAGS_CLASSES = {
    0x1   : 'public', #'ACC_PUBLIC',
    0x2   : 'private', #'ACC_PRIVATE',
    0x4   : 'protected', #'ACC_PROTECTED',
    0x8   : 'static', #'ACC_STATIC',
    0x10  : 'final', #'ACC_FINAL',
    0x200 : 'interface', #'ACC_INTERFACE',
    0x400 : 'abstract', #'ACC_ABSTRACT',
    0x1000: 'synthetic', #'ACC_SYNTHETIC',
    0x2000: 'annotation', #'ACC_ANNOTATION',
    0x4000: 'enum'  #'ACC_ENUM'
}

ACCESS_FLAGS_FIELDS = {
    0x1   : 'public', #'ACC_PUBLIC',
    0x2   : 'private', #'ACC_PRIVATE',
    0x4   : 'protected', #'ACC_PROTECTED',
    0x8   : 'static', #'ACC_STATIC',
    0x10  : 'final', #'ACC_FINAL',
    0x40  : 'volatile', #'ACC_VOLATILE',
    0x80  : 'transient', #'ACC_TRANSIENT',
    0x1000: 'synthetic', #'ACC_SYNTHETIC',
    0x4000: 'enum'  #'ACC_ENUM'
}

ACCESS_FLAGS_METHODS = {
    0x1    : 'public', #'ACC_PUBLIC',
    0x2    : 'private', #'ACC_PRIVATE',
    0x4    : 'protected', #'ACC_PROTECTED',
    0x8    : 'static', #'ACC_STATIC',
    0x10   : 'final', #'ACC_FINAL',
    0x20   : 'synchronized', #'ACC_SYNCHRONIZED',
    0x40   : 'bridge', #'ACC_BRIDGE',
    0x80   : 'varargs', #'ACC_VARARGS',
    0x100  : 'native', #'ACC_NATIVE',
    0x400  : 'abstract', #'ACC_ABSTRACT',
    0x800  : 'strict', #'ACC_STRICT',
    0x1000 : 'synthetic', #'ACC_SYNTHETIC',
    0x10000: '', #'ACC_CONSTRUCTOR',
    0x20000: 'synchronized'  #'ACC_DECLARED_SYNCHRONIZED'
}

def merge_inner(clsdict):
    '''
    Merge the inner class(es) of a class :
    e.g class A { ... } class A$foo{ ... } class A$bar{ ... }
       ==> class A { class foo{...} class bar{...} ... }
    '''
    samelist = False
    while not samelist:
        samelist = True
        classlist = clsdict.keys()
        for classname in classlist:
            parts_name = classname.split('$')
            if len(parts_name) > 2:
                parts_name = ['$'.join(parts_name[:-1]), parts_name[-1]]
            if len(parts_name) > 1:
                mainclass, innerclass = parts_name
                mainclass += ';'
                if mainclass in clsdict:
                    clsdict[mainclass].add_subclass(innerclass, clsdict[classname])
                    del clsdict[classname]
                    samelist = False

def get_type(atype, size=None):
    '''
    Retrieve the type of a descriptor (e.g : (IC)V)
    '''
    res = TYPE_DESCRIPTOR.get(atype)
    if res is None:
        if atype[0] == 'L':
            res = atype[1:-1].replace('/', '.')
        elif atype[0] == '[':
            if size is None:
                res = '%s[]' % get_type(atype[1:])
            else:
                res = '%s[%s]' % (get_type(atype[1:]), size)
        else:
            print 'Unknown descriptor: "%s".' % atype
    return res

def get_new_var(atype):
    '''
    Generator for variables name.
    '''
    for n in count(0):
        yield '%s var%s' % (atype, n)

DEBUG_MODES = {
    'error' : 0,
    'log' : 1,
    'debug' : 2
}

DEBUG_LEVEL = 'log'

def log(s, mode):
    def _log(s):
        print 'LOG: %s' % s
    def _log_debug(s):
        print 'DEBUG: %s' % s
    def _log_error(s):
        print 'ERROR: %s' % s
    if mode is None:
        return
    mode = DEBUG_MODES[mode]
    if mode <= DEBUG_MODES[DEBUG_LEVEL]:
        if mode == DEBUG_MODES['log']:
            _log(s)
        elif mode == DEBUG_MODES['debug']:
            _log_debug(s)
        elif mode == DEBUG_MODES['error']:
            _log_error(s)
