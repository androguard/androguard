SRC	= 	bz2.c


LDFLAGS +=      -lbz2
CFLAGS  +=      -Wall       
mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f
LIBNAME_INSTALL = /usr/local/lib/
LIBNAME_INCLUDE_INSTALL = /usr/local/include/libudis86/

LIBNAME	= libbzip2-wrapper
OBJ	= $(SRC:.c=.o)
EXT_BZ2_OBJ = $(EXT_BZ2_SRC:.c=.o)

.SILENT:

all :   $(EXT_BZ2_OBJ) $(OBJ) $(LIBNAME) tests 
#$(CC) -o bz2final.o $(OBJ) $(EXT_OBJ)

#$(OBJ) 
#$(LIBNAME) tests

$(LIBNAME) :	$(LIBNAME).a 
#$(LIBNAME).so

$(LIBNAME).so :
	$(CC) -o $(LIBNAME).so $(OBJ) -shared $(LDFLAGS)

$(LIBNAME).a :
	echo "  AR    $@"        
	ar r $@ $(OBJ)	
	echo "  RL    $@"        
	ranlib $@

tests :
	$(CC) -c test.c $(CFLAGS)
	$(CC) -o test test.o $(OBJ) $(EXT_BZ2_OBJ) $(LDFLAGS)

install :
	cp $(LIBNAME).so $(LIBNAME_INSTALL)
	cp wrapper.h $(LIBNAME_INCLUDE_INSTALL)

clean :
	$(RM) *.o $(LIBNAME).so $(LIBNAME).a test

%.o   : %.c
	echo " CC $@"
	$(CC) $(CFLAGS) -c -o $@ $<
