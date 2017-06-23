from androguard.misc import AnalyzeDex
from androguard import misc

print(misc.__file__)

from androguard.session import Session
from androguard.core import androconf

s = Session()

androconf.CONF["SESSION"] = s


try:
    h, d, dx = AnalyzeDex("examples/tests/Test.dex")
except:
    d, dx = AnalyzeDex("examples/tests/Test.dex")

z, = d.get_classes()

print(z.source())
