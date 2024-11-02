# -*- coding: utf8- -*-
import unittest

import os

from androguard.core import mutf8
from androguard.core import dex

test_dir = os.path.dirname(os.path.abspath(__file__))


class StringTest(unittest.TestCase):
    def testDex(self):
        with open(os.path.join(test_dir, 'data/APK/StringTests.dex'), "rb") as fd:
            d = dex.DEX(fd.read())

            stests = ["this is a quite normal string",
                      "\u0000 \u0001 \u1234",
                      "使用在線工具將字符串翻譯為中文",
                      "перевод строки на русский с помощью онлайн-инструментов",
                      "온라인 도구를 사용하여 문자열을 한국어로 번역",
                      "オンラインツールを使用して文字列を日本語に翻訳",
                      "This is \U0001f64f, an emoji.",  # complete surrogate
                      "\u2713 check this string",
                      "\uffff \u0000 \uff00",
                      "\u0420\u043e\u0441\u0441\u0438\u044f"]

            for s in stests:
                self.assertIn(s, d.get_strings())

    def testMUTF8(self):
        self.assertEqual("\x67", mutf8.decode(b"\x67"))
        # # Null byte
        self.assertEqual("\x00", mutf8.decode(b"\xc0\x80"))
        self.assertEqual("\uacf0", mutf8.decode(b"\xea\xb3\xb0"))
        # # Surrogates
        self.assertEqual("🙏", mutf8.decode(b"\xed\xa0\xbd\xed\xb9\x8f"))
        self.assertEqual("\U00014f5c", mutf8.decode(b"\xed\xa1\x93\xed\xbd\x9c"))
        # # Lonely surrogates
        # self.assertEqual("\ud853", mutf8.decode(b"\xed\xa1\x93"))
        # self.assertEqual("\udf5c", mutf8.decode(b"\xed\xbd\x9c"))
        # # Normal ASCII String
        self.assertEqual("hello world", mutf8.decode(b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64"))

        # Testing decode

        b = b"\xed\xa1\x93\xed\xbd\x9c" + \
            b"\xed\xa0\xbd\xed\xb9\x8f" + \
            b"\xed\xa0\xbd" + \
            b"\xea\xb3\xb0" + \
            b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64" + \
            b"\xc0\x80"

        self.assertEqual("hello world", mutf8.decode(b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64").encode('utf8',
                                                                                                             errors='backslashreplace').decode(
            'utf8'))
        self.assertEqual("\U00014f5c",
                         mutf8.decode(b"\xed\xa1\x93\xed\xbd\x9c").encode('utf8', errors='backslashreplace').decode(
                             'utf8'))
        self.assertEqual("\U0001f64f",
                         mutf8.decode(b"\xed\xa0\xbd\xed\xb9\x8f").encode('utf8', errors='backslashreplace').decode(
                             'utf8'))
        # self.assertEqual("\\ud853",
                         # mutf8.decode(b"\xed\xa1\x93").encode('utf8', errors='backslashreplace').decode('utf8'))
        # self.assertEqual("\U00024f5c\U0001f64f\\ud83d\uacf0hello world\x00",
        #                  mutf8.decode(b).encode('utf8', errors='backslashreplace').decode('utf8'))

        # Testing encode

        self.assertEqual(b"\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64", mutf8.encode("hello world"))
        self.assertEqual(b"\xed\xa2\x93\xed\xbd\x9c", mutf8.encode("\U00024f5c"))
        self.assertEqual(b"\xed\xa1\xbd\xed\xb9\x8f", mutf8.encode("\U0001f64f"))
        # self.assertEqual(b"\xed\xa1\x93", mutf8.encode("\ud853"))
        # self.assertEqual(b, mutf8.encode("\U00024f5c\U0001f64f\ud83d\uacf0hello world\x00"))


if __name__ == '__main__':
    unittest.main()
