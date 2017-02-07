CD      =       cd
RM      =       rm -f


all :   LIBS DOCS

LIBS :
	${CD} elsim && make

DOCS:
	${CD} docs && make html

clean :
	${CD} elsim && make clean
	${CD} docs && make clean
