from ctypes import cdll, c_long, c_ulong, c_int, c_uint, c_char, c_char_p, POINTER, c_byte, Structure, addressof, byref, c_void_p, create_string_buffer, sizeof, cast

LIBPYLUA_SO = "./libpylua.so"

class PYLUA :
   def __init__(self) :
      self.__lib = cdll.LoadLibrary( LIBPYLUA_SO )
      self.__lib.pylua_init.res_type = c_void_p

      self.__pyl = self.__lib.pylua_init()
      self.__lib.pylua_initlibs(self.__pyl)

   def call(self, msg) :
      self.__lib.pylua_call(self.__pyl, msg, len(msg))
