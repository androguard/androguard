#!/usr/bin/env python

from __future__ import print_function
import sys, hashlib
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

from androguard.session import Session

OUTPUT = "./output/"

TEST = "examples/android/TestsAndroguard/bin/TestActivity.apk"


def display_CFG(d, dx, classes):
    for method in d.get_methods():
        g = dx.get_method(method)

        print(method.get_class_name(), method.get_name(), method.get_descriptor(
        ))
        for i in g.basic_blocks.get():
            print("\t %s %x %x" % (
                i.name, i.start, i.end), '[ NEXT = ', ', '.join(
                    "%x-%x-%s" % (j[0], j[1], j[2].get_name())
                    for j in i.childs), ']', '[ PREV = ', ', '.join(
                        j[2].get_name() for j in i.fathers), ']')


def display_STRINGS(dx):
    print("STRINGS")
    strings = dx.get_strings_analysis()
    for s in strings:
        print(s, " --> ")
        print(strings[s])


def display_FIELDS(d, dx):
    print("FIELDS")
    for f in d.get_fields():
        print(f)
        print(dx.get_field_analysis(f))


def display_PACKAGES(a, x, classes):
    print("CREATED PACKAGES")
    for m, _ in x.get_tainted_packages().get_packages():
        m.show()


def display_PACKAGES_II(a, x, classes):
    # Internal Methods -> Internal Methods
    print("Internal --> Internal")
    for j in x.get_tainted_packages().get_internal_packages():
        analysis.show_Path(a, j)


def display_PACKAGES_IE(a, x, classes):
    # Internal Methods -> External Methods
    print("Internal --> External")
    for j in x.get_tainted_packages().get_external_packages():
        analysis.show_Path(a, j)


def display_SEARCH_PACKAGES(a, x, classes, package_name):
    print("Search package", package_name)
    analysis.show_Paths(a,
                        x.get_tainted_packages().search_packages(package_name))


def display_SEARCH_METHODS(a, x, classes, package_name, method_name,
                           descriptor):
    print("Search method", package_name, method_name, descriptor)
    analysis.show_Paths(a, x.get_tainted_packages().search_methods(
        package_name, method_name, descriptor))


def display_PERMISSION(a, x, classes):
    # Show methods used by permission
    perms_access = x.get_tainted_packages().get_permissions([])
    for perm in perms_access:
        print("PERM : ", perm)
        analysis.show_Paths(a, perms_access[perm])


def display_OBJECT_CREATED(a, x, class_name):
    print("Search object", class_name)
    analysis.show_Paths(a, x.get_tainted_packages().search_objects(class_name))


s = Session()
with open(TEST, "r") as fd:
    s.add(TEST, fd.read())

a, d, dx = s.get_objects_apk(TEST)

print(d.get_strings())
print(d.get_regex_strings("access"))
print(d.get_regex_strings("(long).*2"))
print(d.get_regex_strings(".*(t\_t).*"))

classes = d.get_classes_names()

display_CFG(d, dx, classes)
display_STRINGS(dx)
display_FIELDS(d, dx)
display_PACKAGES(d, dx)
display_PACKAGES_IE(d, dx)
display_PACKAGES_II(d, dx)
display_PERMISSION(d, dx)

display_SEARCH_PACKAGES(dx, "Landroid/telephony/")
display_SEARCH_PACKAGES(dx, "Ljavax/crypto/")
display_SEARCH_METHODS(dx, "Ljavax/crypto/", "generateSecret", ".")

display_OBJECT_CREATED(dx, ".")
