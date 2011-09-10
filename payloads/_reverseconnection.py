# This file is part of pyrasite.
#
# pyrasite is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyrasite is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyrasite.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2011 Red Hat, Inc.

import time, socket, threading

class ReverseConnection(threading.Thread):

    host = '127.0.0.1'    # The remote host
    port = 9001           # The same port as used by the server

    def run(self):
        running = True
        while running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                self.on_connect(s)
                while running:
                    data = s.recv(1024)
                    if data == "quit\n" or len(data) == 0:
                        running = False
                    else:
                        try:
                            running = self.on_command(s, data)
                        except:
                            running = False
                s.close()
            except socket.error, e:
                print(str(e))
            time.sleep(5)

    def on_connect(self, s):
        pass

    def on_command(self, s, cmd):
        raise NotImplementedError("You must prove your own on_command method")
