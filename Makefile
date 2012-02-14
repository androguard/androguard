CD      =       cd
RM      =       rm -f


.SILENT:

all :   LIBS

LIBS :
	cd androguard/core/similarity/libsimilarity && make
	cd androguard/core/bytecodes/libdvm && make
	cd androguard/core/analysis/libsign && make 

clean :
	cd androguard/core/similarity/libsimilarity && make clean
	cd androguard/core/bytecodes/libdvm && make clean
	cd androguard/core/analysis/libsign && make clean
