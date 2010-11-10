#ifndef _PYLUA_H
#define _PYLUA_H

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

#include <lua.h>
#include <lauxlib.h>
#include <lualib.h>

#ifdef PYLUA_DYN

#include <ldo.h>
#include <lfunc.h>
#include <lmem.h>
#include <lobject.h>
#include <lstring.h>
#include <lundump.h>

#endif

#undef DEBUG

#define MAX_PRINT 2048           

typedef struct pylua
{
#ifdef PYLUA_DYN
   int TabOpCodes[MAX_OPCODES];
#endif

   lua_State *L;

} pylua_t;

static inline void DPRINTF(char *Format, ...)
{
   char buffer[MAX_PRINT];
   va_list ap;

   va_start(ap, Format);

   memset(buffer, sizeof(buffer), 0);
   snprintf(buffer, MAX_PRINT-1, "DEBUG [PID(%d)] : %s", getpid(), Format);
   vprintf(buffer, ap);

   va_end(ap);
}

#endif
