from typing import Callable, cast
from mutf8 import decode_modified_utf8, encode_modified_utf8

decode = cast(Callable[[bytes], str], decode_modified_utf8)
encode = cast(Callable[[str], bytes], encode_modified_utf8)