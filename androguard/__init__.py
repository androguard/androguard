import io
import itertools
from functools import update_wrapper
from typing import Iterator

from apkparser import APK
from dexparser import DEX, DEXHelper, MethodHelper


class LazyProperty(property):
    def __init__(self, method, fget=None, fset=None, fdel=None, doc=None):

        self.method = method
        self.cache_name = "_{}".format(self.method.__name__)

        doc = doc or method.__doc__
        super(LazyProperty, self).__init__(
            fget=fget, fset=fset, fdel=fdel, doc=doc
        )

        update_wrapper(self, method)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if hasattr(instance, self.cache_name):
            result = getattr(instance, self.cache_name)
        else:
            if self.fget is not None:
                result = self.fget(instance)
            else:
                result = self.method(instance)

            setattr(instance, self.cache_name, result)

        return result


class Application(object):
    def __init__(self, raw: io.BytesIO):
        self._apk = APK(raw)

        print(self.dex[0].get_type_value(1))

    @LazyProperty
    def dex(self) -> list[DEXHelper]:
        return [
            DEXHelper.from_string(dex_raw)
            for dex_raw in self._apk.get_all_dex()
        ]

    @LazyProperty
    def classes_names(self) -> list[str]:
        return [
            self.dex[0].get_type_value(current_class["class_idx"].value)
            for current_class in self.dex[0].get_classes()
        ]

    @LazyProperty
    def strings(self) -> list[str]:
        l = []
        for dex in self.dex:
            l.extend(dex.get_strings())
        return l

    @LazyProperty
    def methods(self) -> list[MethodHelper]:
        l = []
        for dex in self.dex:
            l.extend(dex.get_methods())
        return l
