SRC	= 	sign.cc

LDFLAGS =	-lm -lbz2 -lz -llzma -lsnappy
CFLAGS  += 	-Wall -I/usr/include/python2.6/
mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f

PATH_SIMILARITY = ../../../classification/libsimilarity/
EXT_SIMILARITY = $(PATH_SIMILARITY)similarity.o
EXT_ZIP = $(PATH_SIMILARITY)z/z.o $(PATH_SIMILARITY)bz2/bz2.o $(PATH_SIMILARITY)smaz/smaz.o $(PATH_SIMILARITY)xz/xz.o $(PATH_SIMILARITY)snappy/snappy.o
EXT_SDK_LZMA = $(PATH_SIMILARITY)lzma/Alloc.o  $(PATH_SIMILARITY)lzma/LzFind.o  $(PATH_SIMILARITY)lzma/LzmaDec.o  $(PATH_SIMILARITY)lzma/LzmaEnc.o  $(PATH_SIMILARITY)lzma/LzmaLib.o  $(PATH_SIMILARITY)lzma/lzma.o

CCP		= g++
CC		= gcc

LIBNAME = libsign

OBJ	= $(SRC:.cc=.o)
AHO_OBJ = ac_heap.o ac_list.o aho_corasick.o
WUMANBER_OBJ = #WuManber.o 
CLUSTER_OBJ = cluster.o

#.SILENT:

all :   AHO CLUSTER $(OBJ) LIBSIGN

AHO :
		$(CC) -c ac_heap.c
		$(CC) -c ac_list.c
		$(CC) -c aho_corasick.c

CLUSTER :
		$(CC) -c cluster.c

WUMANBER :
		$(CCP) WuManber.cpp

LIBSIGN :
	$(CCP) -o $(LIBNAME).so $(OBJ) $(AHO_OBJ) $(WUMANBER_OBJ) $(CLUSTER_OBJ) $(EXT_SIMILARITY) $(EXT_ZIP) $(EXT_SDK_LZMA) -shared $(LDFLAGS)

clean :
	$(RM) *.o $(LIBNAME).so

%.o   : %.cc
	echo " CC $@"
	$(CCP) $(CFLAGS) -c -o $@ $<
