SRC	= 	similarity.c

LDFLAGS =	-lbz2 -lz -llzma
CFLAGS  +=      -Wall       
mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f

EXT_ZIP = z/z.o bz2/bz2.o smaz/smaz.o xz/xz.o
EXT_SDK_LZMA = lzma/Alloc.o  lzma/LzFind.o  lzma/LzmaDec.o  lzma/LzmaEnc.o  lzma/LzmaLib.o  lzma/lzma.o

LIBNAME = "libsimilarity"

OBJ	= $(SRC:.c=.o)

.SILENT:

all :   ZIP $(OBJ) LIBSIMILARITY

ZIP :
	cd z && make
	cd bz2 && make
	cd smaz && make
	cd xz && make
	cd lzma && make
	
LIBSIMILARITY :
	$(CC) -o $(LIBNAME).so $(OBJ) $(EXT_ZIP) $(EXT_SDK_LZMA) -shared $(LDFLAGS)

clean :
	$(RM) *.o $(LIBNAME).so
	cd z && make clean
	cd bz2 && make clean
	cd smaz && make clean
	cd xz && make clean
	cd lzma && make clean

%.o   : %.c
	echo " CC $@"
	$(CC) $(CFLAGS) -c -o $@ $<
