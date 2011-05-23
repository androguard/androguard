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

class wrap_stream(object):
    def __init__(self):
        self.val = ''
    def write(self, s):
        self.val += s
    def clean(self):
        self.val = ''
    def __str__(self):
        return ''.join(self.val)

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

TYPE_LEN = {
    'J': 2,
    'D': 2
}

def get_next_register(params):
    '''
    Return the number of the next register in a generator form.
    '''
    size = 0
    for type in params:
        size += TYPE_LEN.get(type, 1)
        yield size

def get_type_size(param):
    return TYPE_LEN.get(param, 1)

def get_type(atype, size=None):
    '''
    Retrieve the type of a descriptor (e.g : I)
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
            log('Unknown descriptor: "%s".' % atype, 'error')
    return res

def get_params_type(descriptor):
    '''
    Return the parameters type of a descriptor (e.g (IC)V)
    '''
    params = descriptor.split(')')[0][1:].split()
    if params:
        return [param for param in params]
    return []

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
        print '%s' % s
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
