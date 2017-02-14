CD      =       cd
RM      =       rm -f


all :   LIBS DOCS

LIBS :
	${CD} elsim && make

clean :
	${CD} elsim && make clean
