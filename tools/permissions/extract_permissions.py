#!/usr/bin/env python


with open("permi", "r") as f:
    b = f.readlines()

for i in b :
    v = i.split(" ")
    if len(v) > 2 :
        buff = ' '.join( j for j in v[3:] )
        buff = buff[:-1]

        j = 0
        while j < len(buff) and buff[j] == ' ' :
            j += 1

        buff = buff[j:]

        if len(buff) > 1 and buff[-1] != '.' :
            buff += "."

        print "        \"%s\"" % v[2], ":", "\"%s\"," % buff
