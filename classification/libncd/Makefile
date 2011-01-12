SRC	= 	ncd.c

LDFLAGS =	-lbz2 -lz
CFLAGS  +=      -Wall       
mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f

EXT_ZIP = z/z.o bz2/bz2.o smaz/smaz.o

LIBNAME = "libncd"

OBJ	= $(SRC:.c=.o)

.SILENT:

all :   ZIP $(OBJ) LIBNCD 

ZIP :
	cd z && make
	cd bz2 && make
	cd smaz && make
	
LIBNCD :
	$(CC) -o $(LIBNAME).so $(OBJ) $(EXT_ZIP) -shared $(LDFLAGS)

clean :
	$(RM) *.o $(LIBNAME).so
	cd z && make clean
	cd bz2 && make clean
	cd smaz && make clean

%.o   : %.c
	echo " CC $@"
	$(CC) $(CFLAGS) -c -o $@ $<
