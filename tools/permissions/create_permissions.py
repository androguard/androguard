#!/usr/bin/env python

from xml.dom import minidom

MANIFEST = "tools/permissions/AndroidManifest.xml"
STRINGS = "tools/permissions/strings.xml"

NS_ANDROID_URI = 'http://schemas.android.com/apk/res/android'

manifest_document = minidom.parse( MANIFEST )
strings_document = minidom.parse( STRINGS )

dstrings = {}
for i in strings_document.getElementsByTagName( "string" ) :
    try : 
        dstrings[ i.getAttribute( "name") ] = i.firstChild.data 
    except AttributeError :
        pass

for i in manifest_document.getElementsByTagName( "permission" ) :
    label_strings = i.getAttributeNS( NS_ANDROID_URI, "label" )[8:]
    description_strings = i.getAttribute( NS_ANDROID_URI, "description" )[8:]

    rdesc = "\"\""
    rlabel = "\"\""

    if label_strings == "" or description_strings == "" :
        if label_strings != "" :
            rlabel = dstrings[ label_strings ]
        elif description_strings != "" :
            rdesc = dstrings[ description_strings ]
    else :
        rlabel = dstrings[ label_strings ]
        rdesc = dstrings[ description_strings ]
   
    name = i.getAttributeNS(NS_ANDROID_URI, "name")
    name = name[ name.rfind(".") + 1: ]

    print "\t\t\"%s\"" % name, ": [", "\"%s\"" % i.getAttributeNS( NS_ANDROID_URI, "protectionLevel" ), ",", rlabel, ",", rdesc, "],"
