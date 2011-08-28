CD      =       cd
RM      =       rm -f


.SILENT:

all :   LIBS

LIBS :
	cd classification/libsimilarity && make
	cd core/bytecodes/libdvm && make
	cd core/analysis/libsign && make 

clean :
	cd classification/libsimilarity && make clean
	cd core/bytecodes/libdvm && make clean
	cd core/analysis/libsign && make clean
