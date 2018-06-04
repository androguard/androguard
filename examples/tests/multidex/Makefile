all: multidex.apk

%.class: %.java
	javac -source 1.7 -target 1.7 $^

%.apk: com/foobar/foo/Foobar.class com/blafoo/bar/Blafoo.class
	/usr/lib/android-sdk/build-tools/debian/dx --dex --multi-dex --minimal-main-dex --main-dex-list=class_files.txt --output $@ $^
