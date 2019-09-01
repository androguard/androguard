all: Test.dex Switch.dex FillArrays.dex StringTests.dex AnalysisTest.dex ExceptionHandling.dex InterfaceCls.dex FieldsTest.dex

%.class: %.java
	javac -source 1.7 -target 1.7 $^


# Special files with multiple classes...
ExceptionHandling.dex: ExceptionHandling.class SomeException.class AnotherException.class
	/usr/lib/android-sdk/build-tools/debian/dx --dex --output $@ $^

%.dex: %.class
	/usr/lib/android-sdk/build-tools/debian/dx --dex --output $@ $^
