SRC	= 	ncd.c

LDFLAGS =	-lbz2
CFLAGS  +=      -Wall       
mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f

EXT_BZ2 = "bz2/bz2.o"

LIBNAME = "libncd"

OBJ	= $(SRC:.c=.o)

.SILENT:

all :   BZ2 $(OBJ) LIBNCD 
#	tests 

BZ2 :
	cd bz2 && make
	
LIBNCD :
	$(CC) -o $(LIBNAME).so $(OBJ) $(EXT_BZ2) -shared $(LDFLAGS)

tests :
	$(CC) -c test_bz2.c $(CFLAGS)
	$(CC) -o test_bz2 test_bz2.o $(OBJ) $(EXT_BZ2_OBJ) $(LDFLAGS)

install :
	cp $(LIBNAME).so $(LIBNAME_INSTALL)
	cp wrapper.h $(LIBNAME_INCLUDE_INSTALL)

clean :
	$(RM) *.o $(LIBNAME).so
	cd bz2 && make clean

%.o   : %.c
	echo " CC $@"
	$(CC) $(CFLAGS) -c -o $@ $<
