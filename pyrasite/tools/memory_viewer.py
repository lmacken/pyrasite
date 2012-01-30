#!/usr/bin/python
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
# Authors: Luke Macken <lmacken@redhat.com>
"""
An interface for visualizing the output of of the dump-memory payload.

When selecting an object, we attach to the running process and obtain
the value of the object itself.
"""

__version__ = '1.0'

import sys
import urwid
import urwid.raw_display

from meliae import loader

from pyrasite.inspect import ObjectInspector

class PyrasiteMemoryViewer(object):
    palette = [
        ('body',            'black',        'light gray', 'standout'),
        ('header',          'white',        'dark red',   'bold'),
        ('button normal',   'light gray',   'dark blue', 'standout'),
        ('button select',   'white',        'dark green'),
        ('button disabled', 'dark gray',    'dark blue'),
        ('bigtext',         'white',        'black'),
        ('object_output',   'light gray',   'black'),
        ('exit',            'white',        'dark red'),
        ]

    def __init__(self, pid, objects):
        self.inspector = ObjectInspector(pid)
        self.objects = objects
        self.summary = objects.summarize()

    def create_radio_button(self, g, name, obj, fn, disabled=False):
        w = urwid.RadioButton(g, name, False, on_state_change=fn)
        w.obj = obj
        if disabled:
            w = urwid.AttrWrap(w, 'button normal', 'button disabled')
        else:
            w = urwid.AttrWrap(w, 'button normal', 'button select')
        return w

    def create_disabled_radio_button(self, name):
        w = urwid.Text('    ' + name)
        w = urwid.AttrWrap(w, 'button disabled')
        return w

    def display_object(self, w, state):
        if state:
            value = self.inspector.inspect(w.obj.max_address)
            self.object_output.set_text(value)

    def get_object_buttons(self, group=[]):
        buttons = []
        for i, line in enumerate(str(self.summary).split('\n')):
            if i in (0, 1):
                rb = self.create_disabled_radio_button(line)
            else:
                obj = self.summary.summaries[i-2]
                rb = self.create_radio_button(group, line, obj, self.display_object)
            buttons.append(rb)
        return buttons

    def setup_view(self):
        self.object_buttons = self.get_object_buttons()

        # Title
        self.bigtext = urwid.BigText('pyrasite ' + __version__, None)
        self.bigtext.set_font(urwid.Thin6x6Font())
        bt = urwid.Padding(self.bigtext, 'left', None)
        bt = urwid.AttrWrap(bt, 'bigtext')

        # Create the object outpu
        self.object_output = urwid.Text("", wrap='any')
        ca = urwid.AttrWrap(self.object_output, 'object_output')

        # Select the first object
        self.object_buttons[2].set_state(True)

        # ListBox
        obj_out = urwid.Pile([urwid.Divider(), ca])
        objects = urwid.Pile(self.object_buttons)
        l = [objects, obj_out]
        w = urwid.ListBox(urwid.SimpleListWalker(l))

        # Frame
        w = urwid.AttrWrap(w, 'body')
        w = urwid.Frame(header=bt, body=w)

        # Exit message
        exit = urwid.BigText(('exit'," Quit? "), urwid.Thin6x6Font())
        exit = urwid.Overlay(exit, w, 'center', None, 'middle', None)

        return w, exit

    def unhandled_input(self, key):
        if key in ('f8', 'q'):
            self.loop.widget = self.exit_view
            return True
        if self.loop.widget != self.exit_view:
            return
        if key in ('y', 'Y'):
            raise urwid.ExitMainLoop()
        if key in ('n', 'N'):
            self.loop.widget = self.view
            return True

    def main(self):
        self.view, self.exit_view = self.setup_view()
        self.loop = urwid.MainLoop(self.view, self.palette,
            unhandled_input=self.unhandled_input)
        self.loop.run()


def main():
    if len(sys.argv) != 3:
        print "[ pyrasite memory viewer ]\n"
        print "Usage: %s <pid> <objects.json>" % sys.argv[0]
        print "\n    pid - the running process id"
        print "    objects.json - the output of the dump-memory payload"
        print
        sys.exit(1)

    pid = int(sys.argv[1])
    filename = sys.argv[2]
    objects = loader.load(filename)
    objects.compute_referrers()

    PyrasiteMemoryViewer(pid=pid, objects=objects).main()


if '__main__' == __name__:
    main()
