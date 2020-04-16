Parsing Instructions and Bytecode
=================================

One often requested task is to parse the bytecode of all (or certain) methods.
The bytecode can be used for various tasks, from creating simple statistics to machine learning.

The bytecode is stored for each method in the Dalvik file.
Google provides some documentation about the `bytecode format <https://source.android.com/devices/tech/dalvik/dalvik-bytecode>`_, which is very useful
if you want to process it.
Androguard can provide three different forms of the bytecode:

* Raw bytes
* disassembled representation
* decompiled representation

All three serve different purposes and might be used at the same time.

First of all, we need to know a few things about the differences of representation.
While the documentation says, that bytecode is structured in 16bit units, Androguard will use 8bit units
to show the bytecode (i.e. :code:`bytes`).
If offsets are given in the bytecode, they are also presented as bytes. Also all indices are provided in byte length.
Other than that, the mnemonic representation should follow in large parts the one provided in the documentation.
Arguments are always shown in their "expanded" form, which is especially important for the few opcodes where only
parts of the value are stores, like :code:`const/high16`. In this case, the full value is shown including the
16 lower zero bits.
As Dalvik is closely related to Java, all integer values are represented as signed :code:`int` (32bit value) or :code:`long` (64bit).
Values are either given in decimal or hexadecimal representation.
If the value is hexadecimal, the value is suffixed with a :code:`h`, i.e. :code:`f7a0h` or :code:`63392`.

In the following few examples, we will take the provided APK file :code:`examples\android\TestsAndroguard\bin\TestActivity.apk`
and assume that you have loaded it via :code:`AnalyzeAPK` and have the following objects:

.. code-block:: guess

    >>> a
    <androguard.core.bytecodes.apk.APK object at 0x00000000058DD240>
    >>> d
    [<androguard.core.bytecodes.dvm.DalvikVMFormat object at 0x0000000004CE4CF8>]
    >>> dx
    <analysis.Analysis VMs: 1, Classes: 492, Strings: 496>


Getting the raw bytecode
------------------------

Our first task is to extract the raw bytecode of all methods.

.. code-block:: python

    for method in dx.get_methods():
        if method.is_external():
            continue
        # Need to get the EncodedMethod from the MethodClassAnalysis object
        m = method.get_method()
        if m.get_code():
            # get_code() returns None or a DalvikCode object
            # get_bc() returns a DCode object
            # get_raw() returns bytearray
            print(m.get_code().get_bc().get_raw())


This will print a lot of bytearrays.


Getting disassembled instructions
---------------------------------

Next, we would like to get the disassembled instructions.
The instruction itself have many different methods and you can find a detailed description in the documentation
of the :class:`~androguard.core.bytecodes.dvm.Instruction` class.

.. code-block:: python

    for method in dx.get_methods():
        if method.is_external():
            continue
        m = method.get_method()
        for idx, ins in m.get_instructions_idx():
            print(idx, ins.get_op_value(), ins.get_name(), ins.get_output())


This will print something like:

.. code-block:: none

    0 91 iput-object v1, v0, LTestDefaultPackage$TestInnerClass$TestInnerInnerClass;->this$1 LTestDefaultPackage$TestInnerClass;
    4 112 invoke-direct v0, Ljava/lang/Object;-><init>()V
    10 89 iput v2, v0, LTestDefaultPackage$TestInnerClass$TestInnerInnerClass;->a I
    14 89 iput v3, v0, LTestDefaultPackage$TestInnerClass$TestInnerInnerClass;->c I
    18 14 return-void

The variable :code:`idx` is the index counted in bytes where the opcode starts.
:code:`ins.get_op_value()` returns the integer value of the opcode, :code:`ins.get_name()` the mnemonic
and :code:`ins.get_output()` the parsed arguments.

If you want to get the disassembled instructions from given specific class_name and method_name, you can follow the example as shown below.

.. code-block:: python

    for m in dx.find_methods("Ltests/androguard/TestActivity;","foo"):
        print(m.full_name)
        for idx, ins in m.get_method().get_instructions_idx():
            print(idx, ins.get_op_value(), ins.get_name(), ins.get_output())


The output will look like:

.. code-block:: none

    Ltests/androguard/TestActivity; foo (I I)I
    0 1 move v0, v4
    2 52 if-lt v3, v0, +005h
    6 57 if-nez v3, +00eh
    10 15 return v0
    12 216 add-int/lit8 v4, v0, 1
    16 147 div-int v3, v0, v3
    20 1 move v0, v4
    22 40 goto -ah
    24 13 move-exception v1
    26 19 const/16 v3, 10

As an example, let's count the number of individual opcodes and create some statistics:

.. code-block:: python

    from collections import defaultdict
    from operator import itemgetter
    c = defaultdict(int)

    for method in dx.get_methods():
        if method.is_external():
            continue
        m = method.get_method()
        for ins in m.get_instructions():
            c[(ins.get_op_value(), ins.get_name())] += 1

    for k, v in sorted(c.items(), key=itemgetter(1), reverse=True)[:10]:
        print(k, '-->',  v)

This will output the top ten opcodes and the count:

.. code-block:: none

    (110, 'invoke-virtual') --> 3532
    (84, 'iget-object') --> 2223
    (12, 'move-result-object') --> 1749
    (18, 'const/4') --> 1156
    (112, 'invoke-direct') --> 1130
    (10, 'move-result') --> 1111
    (14, 'return-void') --> 1106
    (56, 'if-eqz') --> 898
    (26, 'const-string') --> 806
    (113, 'invoke-static') --> 755


As another example, we will collect all constant integer values:

.. code-block:: python

    c = set()

    for method in dx.get_methods():
        if method.is_external():
            continue
        m = method.get_method()
        for ins in m.get_instructions():
            if 0x12 <= ins.get_op_value() <= 0x19:
                c.add(ins.get_literals()[0])

    print('minimal:', min(c))
    print('maximal:', max(c))
    print('length: ', len(c))

This will print:

.. code-block:: none

    minimal: -4616189618054758400
    maximal: 4707499256968118272
    length:  205

Get processed bytecode from decompiler
--------------------------------------

The last topic is how to get the processed bytecode from the decompiler.
If you are only interested in the decompiled source code, you can use the :code:`source()` function:

.. code-block:: python

    for method in dx.get_methods():
        if method.is_external():
            continue
        m = method.get_method()
        print(m.source())

It will print all sources of all methods.

But, you can also use DAD to compile abstract syntax trees (AST) for you.
An AST can easily be used to do analysis on the code itself.
Unfortunately, the method to get to the AST is a little bit awkward:

.. code-block:: python

    from pprint import pprint
    from androguard.decompiler.dad.decompile import DvMethod
    for method in dx.get_methods():
        if method.is_external():
            continue
        dv = DvMethod(method)
        dv.process(doAST=True)
        pprint(dv.get_ast())

The AST is a dictionary, which might look like this one:

.. code-block:: none

    {'body': ['BlockStatement',
              None,
              [['ExpressionStatement',
                ['Assignment',
                 [['FieldAccess',
                   [['Local', 'this']],
                   (TestDefaultPackage$TestInnerClass$TestInnerInnerClass,
                    this$1,
                    LTestDefaultPackage$TestInnerClass;)],
                  ['Local', 'p1']],
                 '']],
               ['ExpressionStatement',
                ['Assignment',
                 [['FieldAccess',
                   [['Local', 'this']],
                   (TestDefaultPackage$TestInnerClass$TestInnerInnerClass, a, I)],
                  ['Local', 'p2']],
                 '']],
               ['ExpressionStatement',
                ['Assignment',
                 [['FieldAccess',
                   [['Local', 'this']],
                   (TestDefaultPackage$TestInnerClass$TestInnerInnerClass, c, I)],
                  ['Local', 'p3']],
                 '']],
               ['ReturnStatement', None]]],
    'comments': [],
     'flags': ['private'],
     'params': [[['TypeName', (TestDefaultPackage$TestInnerClass, 0)],
                 ['Local', 'p1']],
                [['TypeName', ('.int', 0)], ['Local', 'p2']],
                [['TypeName', ('.int', 0)], ['Local', 'p3']]],
     'ret': ['TypeName', ('.void', 0)],
     'triple': (TestDefaultPackage$TestInnerClass$TestInnerInnerClass,
                <init>,
                (LTestDefaultPackage$TestInnerClass;II)V)}

This AST is the equivalent of the following source code:

.. code-block:: java

    private TestDefaultPackage$TestInnerClass$TestInnerInnerClass(TestDefaultPackage$TestInnerClass p1, int p2, int p3)
    {
        this.this$1 = p1;
        this.a = p2;
        this.c = p3;
        return;
    }

