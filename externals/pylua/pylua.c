#include <pylua.h>

/* Initialize lua with dynamics opcodes */
int pylua_dyn(pylua_t *pyl, int *TabOpCodesVM)
{
   int error = 0;
  
//   luaL_initopcodes(pyl->L, TabOpCodesVM);   
   return error;
}

/* Initialize the creator of the master VM lua */
pylua_t* pylua_init()
{
   int error = 0;
   
   pylua_t *pyl = malloc(sizeof(pylua_t));

   if (pyl == NULL)
      return NULL;

#ifdef DEBUG
   DPRINTF("Init PYLUA ...\n");
#endif

   pyl->L = lua_open();
   
   return pyl;
}

int pylua_initlibs(pylua_t *pyl)
{
   int error;

   if (pyl == NULL || pyl->L == NULL)
      return -1;

#ifdef DEBUG
   DPRINTF("Init LIBS PYLUA ...\n");
#endif

   luaL_openlibs(pyl->L);
   luaopen_bit(pyl->L);

   return error;
}
/*
int pylua_writer_size(lua_State* L, const void* p, size_t size, void* u)
{
   size_t *psize = u;

   *psize = *psize + size;

   return 0;
}


int pylua_writer(lua_State* L, const void* p, size_t size, void* u)
{
   pybuffer_t *out = (pybuffer_t *)u;

   memcpy(out->code + out->len, p, size);
   out->len = out->len + size;

   return 0;
}

#define toproto(L,i) (clvalue(L->top+(i))->l.p)
*/

int pylua_call(pylua_t *pyl, char *in, unsigned int len)
{
   int error;
   size_t size_bytecode;

   error = luaL_loadbuffer(pyl->L, in, len, "pylua") || lua_pcall(pyl->L, 0, 0, 0);
   if (error)
      {
         fprintf(stderr, "%s\n", lua_tostring(pyl->L, -1));
         lua_pop(pyl->L, 1);
         return error;
      }

#ifdef PYLUA_DYN
   Proto *f = toproto(pyl->L, -1);
   luaU_print(pyl->L, f, 1);

   lua_lock(pyl->L);
  
   size_bytecode = 0;
   luaU_dump(pyl->L, f, pylua_writer_size, &size_bytecode, 0);
   
   pbt_out->len = 0;
   pbt_out->code = malloc(size_bytecode);
   luaU_dump(pyl->L, f, pylua_writer, pbt_out, 0);

   lua_unlock(pyl->L); 
#endif

   return error;
}
