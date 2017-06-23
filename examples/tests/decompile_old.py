from androguard.misc import AnalyzeDex

d, dx = AnalyzeDex("Test.dex")

z, = d.get_classes()

print(z.source())
