# "meliae" provides a way to dump python memory usage information to a JSON
# disk format, which can then be parsed into useful things like graph
# representations.
#
# https://launchpad.net/meliae
# http://jam-bazaar.blogspot.com/2009/11/memory-debugging-with-meliae.html

import os
import tempfile

import meliae.scanner

path = os.path.join(tempfile.gettempdir(), "pyrasite-%d-objects.json" % os.getpid())
meliae.scanner.dump_all_objects(path)
