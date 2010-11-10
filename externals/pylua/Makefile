include config.h

SRC	= 	pylua.c bit.c

mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f

LIBNAME	= libpylua

LDFLAGS += -llua5.1   
#-L$(POLARSSLPATH) -lpolarssl
#$(POLARSSLLIB)
CFLAGS  +=      -I./ -I$(LUAPATH)
#-I../core/ -I$(POLARSSLPATH_INCLUDE)

OBJ	= $(SRC:.c=.o)


.SILENT:

all :   $(OBJ) $(LIBNAME) 


LUA :
	$(CD) $(LUAPATH) && make linux


$(LIBNAME) :	$(LIBNAME).so $(LIBNAME).a 
$(LIBNAME).so :
	$(CC) -o $(LIBNAME).so $(OBJ) $(LDFLAGS) -shared
$(LIBNAME).a :
	echo "  AR    $@"        
	ar rcu $@ $(OBJ)	
	echo "  RL    $@"        
	ranlib $@

#install :
#	cp $(LIBNAME).so $(LIBNAME_INSTALL)
#	cp wrapper.h $(LIBNAME_INCLUDE_INSTALL)

clean :
	$(RM) *.o $(LIBNAME).* 

%.o   : %.c
	echo " CC $@"
	$(CC) $(CFLAGS) -c -o $@ $<
