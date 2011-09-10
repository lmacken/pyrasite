import sys

for name in sorted(sys.modules):
    print('%s: %s' % (name, sys.modules[name]))
