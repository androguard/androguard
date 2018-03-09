all: Test.dex Switch.dex FillArrays.dex StringTests.dex AnalysisTest.dex

%.class: %.java
	javac -source 1.7 -target 1.7 $^

%.dex: %.class
	/usr/lib/android-sdk/build-tools/debian/dx --dex --output $@ $^
