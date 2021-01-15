Other tools that are useful for androguard.

# Androdecomp

- To decompile a given method: `androdecomp.py --input THEAPK --classname CLASSNAME --methodname METHODNAME`
- To decompile an entire class: `androdecomp.py --input THEAPK --classname CLASSNAME`
- To list class: `androdecomp.py --input THEAPK`
- To list methods of a given class: ``androdecomp.py --input THEAPK --classname CLASSNAME --list`

Example:

```
python3 androclass.py --input 885d07d1532dcce08ae8e0751793ec30ed0152eee3c1321e2d051b2f0e3fa3d7.apk --classname 'Lcom/android/tester/C11;' --methodname 'Lcom/android/tester/C11; a ()V'
Analyzing 885d07d1532dcce08ae8e0751793ec30ed0152eee3c1321e2d051b2f0e3fa3d7.apk...
Decompiling method...
public void a()
    {
        new Thread(new com.android.tester.C11$23(this)).start();
        return;
    }
```
