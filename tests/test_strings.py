# -*- coding: utf8- -*-
import unittest

import sys

from androguard.core.bytecodes import dvm, mutf8
from androguard.core.analysis import analysis


class StringTest(unittest.TestCase):
    def testDex(self):
        with open("examples/tests/StringTests.dex", "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())

            stests = [u"this is a quite normal string",
                      u"\u0000 \u0001 \u1234",
                      u"使用在線工具將字符串翻譯為中文",
                      u"перевод строки на русский с помощью онлайн-инструментов",
                      u"온라인 도구를 사용하여 문자열을 한국어로 번역",
                      u"オンラインツールを使用して文字列を日本語に翻訳",
                      u"This is \U0001f64f, an emoji.",  # complete surrogate
                      u"\u2713 check this string",
                      u"\uffff \u0000 \uff00",
                      u"\u0420\u043e\u0441\u0441\u0438\u044f"]

            for s in stests:
                self.assertIn(s, d.get_strings())

    def testMUTF8(self):
        self.assertEqual(u"\x67", mutf8.decode(b"\x67"))
        # Null byte
        self.assertEqual(u"\x00", mutf8.decode(b"\xc0\x80"))
        self.assertEqual(u"\uacf0", mutf8.decode(b"\xea\xb3\xb0"))
        # Surrogates
        self.assertEqual(u"\ud83d\ude4f", mutf8.decode(b"\xed\xa0\xbd\xed\xb9\x8f"))
        self.assertEqual(u"\ud853\udf5c", mutf8.decode(b"\xed\xa1\x93\xed\xbd\x9c"))
        # Lonely surrogates
        self.assertEqual(u"\ud853", mutf8.decode(b"\xed\xa1\x93"))
        self.assertEqual(u"\udf5c", mutf8.decode(b"\xed\xbd\x9c"))
        # Normal ASCII String
        self.assertEqual(u"hello world", mutf8.decode(b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64"))

        # Test the patching of strings

        self.assertEqual(u"hello world", mutf8.patch_string(mutf8.decode(b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64")))
        self.assertEqual(u"\U00024f5c", mutf8.patch_string(mutf8.decode(b"\xed\xa1\x93\xed\xbd\x9c")))
        self.assertEqual(u"\U0001f64f", mutf8.patch_string(mutf8.decode(b"\xed\xa0\xbd\xed\xb9\x8f")))
        self.assertEqual(u"\\ud853", mutf8.patch_string(mutf8.decode(b"\xed\xa1\x93")))

        b = b"\xed\xa1\x93\xed\xbd\x9c" + \
            b"\xed\xa0\xbd\xed\xb9\x8f" + \
            b"\xed\xa0\xbd" + \
            b"\xea\xb3\xb0" + \
            b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64" + \
            b"\xc0\x80"

        self.assertEqual(u"\U00024f5c\U0001f64f\\ud83d\uacf0hello world\x00", mutf8.patch_string(mutf8.decode(b)))



if __name__ == '__main__':
    unittest.main()
