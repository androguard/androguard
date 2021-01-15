import androguard.misc
import argparse

def get_arguments():
    parser = argparse.ArgumentParser(description='Decompile a given class or method using Androguard' )
    parser.add_argument('-i','--input', help='filename of the APK to parse', action='store', required=True)
    parser.add_argument('-c','--classname', help='class name. Something like Lcom/android/tester/C11;', action='store')
    parser.add_argument('-m','--methodname', help='method full name. Something like: Lcom/android/tester/C7; <init> ()V', action='store')
    parser.add_argument('-l', '--list', help='list methods or classes. To list methods of a class, provide also --classname argument.', action='store_true')
    args = parser.parse_args()
    return args

def decompile_class(dx, classname):
    try:
        dx.classes[classname].get_vm_class().source()
    except KeyError as e:
        print("decompile_class(): unknown class={} exception={}".format(classname, e))

def decompile_method(dx, classname, methodname):
    try:
        for method in dx.classes[classname].get_vm_class().get_methods():
            if method.full_name == methodname:
                method.source()
    except KeyError as e:
        print("decompile_method(): unknown class={} exception={}".format(classname, e))

def list_classes(dx):
    l = []
    for c in dx.get_classes():
        l.append(c.name)
    return l

def list_methods(dx, classname):
    l = []
    try:
        for method in dx.classes[classname].get_vm_class().get_methods():
            l.append(method.full_name)
    except KeyError as e:
        print("list_methods(): unknown class={} exception={}".format(classname, e))
    return l
    

def main(args):
    print("Analyzing {}...".format(args.input))
    a, d, dx = androguard.misc.AnalyzeAPK(args.input)

    if args.classname and args.methodname:
        print("Decompiling method...")
        decompile_method(dx, args.classname, args.methodname)
        
    elif args.classname and args.list:
        print("List of methods in class={}".format(args.classname))
        for m in list_methods(dx, args.classname):
            print("- {}".format(m))
                  
    elif args.classname:
        print("Decompiling entire class...")
        decompile_class(dx. args.classname)
                  
    else:
        print("List of classes: ")
        for c in list_classes(dx):
            print("- {}".format(c))


if __name__ == "__main__":
    args = get_arguments()
    main(args)
