from ctypes import (cdll, Structure, Union, sizeof, addressof, create_string_buffer, c_byte, c_ubyte, c_char, c_short, c_ushort, c_int, c_uint, c_ulong, c_char_p, c_void_p, c_ulonglong, c_longlong)


u = cdll.LoadLibrary( "./libncd/libncd.so" )
print u

TEST1 = "TOTOO"
TEST2 = "OUPS LA BOOOM"

u.ncd( TEST1, len(TEST1),
       TEST2, len(TEST2)
      )
