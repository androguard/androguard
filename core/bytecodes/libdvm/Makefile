SRC	= 	dvm.cc

LDFLAGS = 
CFLAGS  += 	-Wall       
mkdir	=	mkdir -p
CD      =       cd
RM      =       rm -f

CCP		= g++
CC		= gcc

LIBNAME = libdvm

OBJ	= $(SRC:.c=.o)

#.SILENT:

all :   $(OBJ) LIBDVM

LIBDVM :
	$(CCP) -o $(LIBNAME).so $(OBJ) -shared $(LDFLAGS)

clean :
	$(RM) *.o $(LIBNAME).so

%.o   : %.c
	echo " CC $@"
	$(CCP) $(CFLAGS) -c -o $@ $<
