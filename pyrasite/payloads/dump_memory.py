# "meliae" provides a way to dump python memory usage information to a JSON
# disk format, which can then be parsed into useful things like graph
# representations.
#
# https://launchpad.net/meliae
# http://jam-bazaar.blogspot.com/2009/11/memory-debugging-with-meliae.html

import os, meliae.scanner
meliae.scanner.dump_all_objects('/tmp/pyrasite-%d-objects.json' % os.getpid())
