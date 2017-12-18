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
                      u"This is \U0001f64f, an emoji.",
                      u"\u2713 check this string",
                      u"\uFFFF \u0000 \uFF00",
                      u"\u0420\u043e\u0441\u0441\u0438\u044f"]

            for s in stests:
                self.assertIn(s, d.get_strings())

    def testMUTF8(self):
        self.assertEqual(u"\x67", mutf8.decode(b"\x67"))
        self.assertEqual(u"\x00", mutf8.decode(b"\xc0\x80"))
        self.assertEqual(u"\uacf0", mutf8.decode(b"\xea\xb3\xb0"))
        self.assertEqual(u"\ud83d\ude4f", mutf8.decode(b"\xed\xa0\xbd\xed\xb9\x8f"))


if __name__ == '__main__':
    unittest.main()
