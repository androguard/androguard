#ifndef _SMAZ_H
#define _SMAZ_H

int sCompress(int level, void *in, unsigned int inlen, void *out, unsigned int *outlen);
int smaz_compress(char *in, int inlen, char *out, int outlen);

#endif
