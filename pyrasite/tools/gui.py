#!/usr/bin/env python
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
# Copyright (C) 2012 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import os
import sys
import time
import psutil
import keyword
import tokenize

from meliae import loader
from gi.repository import GLib, GObject, Pango, GdkPixbuf, Gtk

import pyrasite
from pyrasite.utils import run, setup_logger
from pyrasite.ipc import PyrasiteIPC

log = logging.getLogger('pyrasite')


class Process(GObject.GObject):

    def __init__(self, pid):
        super(Process, self).__init__()
        self.pid = pid
        self.title = run('ps --no-heading -o cmd= -p %d' % pid)[1]
        self.command = self.title
        self.title = self.title[:25]
        self.ipc = None
        self.filename = None

    def connect(self):
        """
        Setup a communication socket with the process by injecting
        a reverse subshell and having it connect back to us.
        """
        self.ipc = PyrasiteIPC(self.pid)
        self.ipc.inject()
        self.ipc.listen()

    def cmd(self, cmd, *args, **kw):
        return self.ipc.cmd(cmd, *args, **kw)

    def close(self):
        print "Closing %r" % self
        self.ipc.close()

    def __repr__(self):
        return "<Process %d '%s'>" % (self.pid, self.title)

    def __str__(self):
        return self.title


class ProcessTreeStore(Gtk.TreeStore):
    """ This TreeStore finds all running python processes.  """

    def __init__(self, *args):
        Gtk.TreeStore.__init__(self, str, Process, Pango.Style)
        for pid in os.listdir('/proc'):
            try:
                pid = int(pid)
                proc = Process(pid)
                try:
                    maps = open('/proc/%d/maps' % pid).read().strip()
                    if 'python' in maps:
                        self.append(None, (proc.title, proc, Pango.Style.NORMAL))
                except IOError:
                    pass
            except ValueError:
                pass


class InputStream(object):
    '''
    Simple Wrapper for File-like objects. [c]StringIO doesn't provide
    a readline function for use with generate_tokens.
    Using a iterator-like interface doesn't succeed, because the readline
    function isn't used in such a context. (see <python-lib>/tokenize.py)
    '''
    def __init__(self, data):
        self.__data = [ '%s\n' % x for x in data.splitlines() ]
        self.__lcount = 0

    def readline(self):
        try:
            line = self.__data[self.__lcount]
            self.__lcount += 1
        except IndexError:
            line = ''
            self.__lcount = 0

        return line


class PyrasiteWindow(Gtk.Window):

    def __init__(self):
        super(PyrasiteWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)

        self.processes = {}
        self.pid = None # Currently selected pid

        self.set_title('Pyrasite v%s' % pyrasite.__version__)
        self.set_default_size (600, 400)

        hbox = Gtk.HBox(homogeneous=False, spacing=0)
        self.add(hbox)

        tree = self.create_tree()
        hbox.pack_start(tree, False, False, 0)

        notebook = Gtk.Notebook()

        main_vbox = Gtk.VBox()
        main_vbox.pack_start(notebook, True, True, 0)
        self.progress = Gtk.ProgressBar()
        main_vbox.pack_end(self.progress, False, False, 0)
        hbox.pack_start(main_vbox, True, True, 0)

        (text_widget, info_buffer) = self.create_text(False)
        notebook.append_page(text_widget, Gtk.Label.new_with_mnemonic('_Info'))
        self.info_buffer = info_buffer
        self.info_buffer.create_tag('title', font = 'Sans 18')

        (stacks_widget, source_buffer) = self.create_text(True)
        notebook.append_page(stacks_widget, Gtk.Label.new_with_mnemonic('_Stacks'))

        self.source_buffer = source_buffer
        self.source_buffer.create_tag('bold', weight=Pango.Weight.BOLD)
        self.source_buffer.create_tag('italic', style=Pango.Style.ITALIC)
        self.source_buffer.create_tag('comment', foreground='#c0c0c0')
        self.source_buffer.create_tag('decorator', foreground='#7d7d7d',
                                      style=Pango.Style.ITALIC)
        self.source_buffer.create_tag('keyword', foreground='#0000ff')
        self.source_buffer.create_tag('number', foreground='#800000')
        self.source_buffer.create_tag('string', foreground='#00aa00',
                                      style=Pango.Style.ITALIC)

        self.obj_tree = obj_tree = Gtk.TreeView()
        self.obj_store = obj_store = Gtk.ListStore(str, int, int, int,
                                                   int, int, int, str)
        obj_tree.set_model(obj_store)
        obj_selection = obj_tree.get_selection()
        obj_selection.set_mode(Gtk.SelectionMode.BROWSE)
        obj_tree.set_size_request(200, -1)

        columns = [
            Gtk.TreeViewColumn(title = 'Count',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 1, style = 2),
            Gtk.TreeViewColumn(title = '%',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 2, style = 2),
            Gtk.TreeViewColumn(title = 'Size',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 3, style = 2),
            Gtk.TreeViewColumn(title = '%',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 4, style = 2),
            Gtk.TreeViewColumn(title = 'Cumulative',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 5, style = 2),
            Gtk.TreeViewColumn(title = 'Max',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 6, style = 2),
            Gtk.TreeViewColumn(title = 'Kind',
                               cell_renderer = Gtk.CellRendererText(),
                               text = 7, style = 2),
            ]

        first_iter = obj_store.get_iter_first()
        if first_iter is not None:
            obj_selection.select_iter(first_iter)

        obj_selection.connect('changed', self.obj_selection_cb, obj_store)
        obj_tree.connect('row_activated', self.obj_row_activated_cb, obj_store)

        for i, column in enumerate(columns):
            column.set_sort_column_id(i + 1)
            obj_tree.append_column(column)

        obj_tree.collapse_all()
        obj_tree.set_headers_visible(True)

        scrolled_window = Gtk.ScrolledWindow(hadjustment = None,
                                             vadjustment = None)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(obj_tree)

        hbox = Gtk.VBox(homogeneous=False, spacing=0)

        bar = Gtk.InfoBar()
        hbox.pack_start(bar, False, False, 0)
        bar.set_message_type(Gtk.MessageType.INFO)
        self.obj_totals = Gtk.Label()
        bar.get_content_area().pack_start(self.obj_totals, False, False, 0)
        hbox.pack_start(bar, False, False, 0)

        hbox.pack_start(scrolled_window, True, True, 0)
        (text_widget, obj_buffer) = self.create_text(False)
        self.obj_buffer = obj_buffer
        hbox.pack_end(text_widget, True, True, 0)

        notebook.append_page(hbox, Gtk.Label.new_with_mnemonic('_Objects'))

        (shell_view, shell_widget, shell_buffer) = self.create_text(False, return_view=True)
        self.shell_view = shell_view
        self.shell_buffer = shell_buffer
        self.shell_widget = shell_widget
        shell_hbox = Gtk.VBox()
        shell_hbox.pack_start(shell_widget, True, True, 0)
        shell_bottom = Gtk.HBox()
        shell_prompt = Gtk.Entry()
        self.shell_prompt = shell_prompt
        shell_bottom.pack_start(shell_prompt, True, True, 0)
        shell_button = Gtk.Button('Run')
        shell_button.connect('clicked', self.run_shell_command)
        shell_bottom.pack_start(shell_button, False, False, 0)
        shell_hbox.pack_end(shell_bottom, False, False, 0)

        notebook.append_page(shell_hbox, Gtk.Label.new_with_mnemonic('_Shell'))

        # To try and grab focus of our text input
        notebook.connect('switch-page', self.switch_page)
        self.notebook = notebook

        self.call_graph = Gtk.Image()
        scrolled_window = Gtk.ScrolledWindow(hadjustment = None,
                                             vadjustment = None)
        scrolled_window.set_policy(Gtk.PolicyType.ALWAYS,
                                   Gtk.PolicyType.ALWAYS)

        scrolled_window.add_with_viewport(self.call_graph)

        notebook.append_page(scrolled_window, Gtk.Label.new_with_mnemonic('_Call Graph'))

        self.show_all()
        self.progress.hide()

    def switch_page(self, notebook, page, pagenum):
        name = self.notebook.get_tab_label(self.notebook.get_nth_page(pagenum))
        if name.get_text() == 'Shell':
            # FIXME:
            self.shell_prompt.grab_focus()

    def run_shell_command(self, widget):
        cmd = self.shell_prompt.get_text()
        end = self.shell_buffer.get_end_iter()
        self.shell_buffer.insert(end, '\n>>> %s\n' % cmd)
        print "run_shell_command(%r)" % cmd
        output = self.proc.cmd(cmd)
        print repr(output)
        self.shell_buffer.insert(end, output)
        self.shell_prompt.set_text('')

        insert_mark = self.shell_buffer.get_insert()
        self.shell_buffer.place_cursor(self.shell_buffer.get_end_iter())
        self.shell_view.scroll_to_mark(insert_mark , 0.0, True, 0.0, 1.0)

    def obj_selection_cb(self, selection, model):
        sel = selection.get_selected()
        treeiter = sel[1]
        addy = model.get_value(treeiter, 0)
        inspector = pyrasite.ObjectInspector(self.pid)
        value = inspector.inspect(addy)
        self.obj_buffer.set_text(value)

    def obj_row_activated_cb(self, *args, **kw):
        print "obj_row_activated_cb(%s, %s)" % (args, kw)

    def generate_description(self, proc, title):
        d = ''
        p = psutil.Process(proc.pid)

        cputimes = p.get_cpu_times()
        d += '\nCPU usage: %0.2f%% (%s user, %s system)\n' % (
                p.get_cpu_percent(interval=1.0),
                cputimes.user, cputimes.system)

        meminfo = p.get_memory_info()
        d += 'Memory usage: %0.2f%% (%s RSS, %s VMS)\n\n' % (
                p.get_memory_percent(),
                meminfo.rss, meminfo.vms)

        d += '[ Open Files ]'
        for open_file in p.get_open_files():
            d += '\n' + str(open_file)

        d += '\n\n[ Connections ]'
        for conn in p.get_connections():
            d += '\n' + str(conn)

        d += '\n\n[ Threads ]'
        for thread in p.get_threads():
            d += '\n' + str(thread)

        io = p.get_io_counters()
        d += '\n\n[ IO ]\nread count: %s\n' % io.read_count
        d += 'read bytes: %s\n' % io.read_bytes
        d += 'write count: %s\n' % io.write_count
        d += 'write bytes: %s\n' % io.write_bytes

        d += '\n[ Details ]\n'
        d += 'status: %s\n' % p.status
        d += 'cwd: %s\n' % p.getcwd()
        d += 'cmdline: %s\n' % ' '.join(p.cmdline)
        d += 'terminal: %s\n' % p.terminal
        d += 'created: %s\n' % time.ctime(p.create_time)
        d += 'username: %s\n' % p.username
        d += 'uid: %s\n' % p.uids.real
        d += 'gid: %s\n' % p.gids.real
        d += 'nice: %s\n\n' % p.nice

        # output and style the title
        (start, end) = self.info_buffer.get_bounds()
        self.info_buffer.delete(start, end)
        (start, end) = self.source_buffer.get_bounds()
        self.source_buffer.delete(start, end)

        start = self.info_buffer.get_iter_at_offset(0)
        end = start.copy()
        self.info_buffer.insert(end, title)
        start = end.copy()
        start.backward_chars(len(title))
        self.info_buffer.apply_tag_by_name('title', start, end)
        self.info_buffer.insert(end, '\n')

        # output the description
        self.info_buffer.insert(end, d)

    def update_progress(self, fraction, text=None):
        if text:
            self.progress.set_text(text + '...')
            self.progress.set_show_text(True)
        if fraction:
            self.progress.set_fraction(fraction)
        else:
            self.progress.pulse()
        while Gtk.events_pending():
            Gtk.main_iteration()

    def selection_cb(self, selection, model):
        sel = selection.get_selected()
        if sel == ():
            return

        self.progress.show()
        self.update_progress(0.1, "Analyzing process")

        treeiter = sel[1]
        title = model.get_value(treeiter, 0)
        proc = model.get_value(treeiter, 1)
        self.proc = proc
        self.pid = proc.pid

        # Analyze the process
        self.generate_description(proc, title)

        # Inject a reverse subshell
        self.update_progress(0.2, "Injecting backdoor")
        if proc.title not in self.processes:
            proc.connect()
            self.processes[proc.title] = proc

        # Dump objects and load them into our store
        self.update_progress(0.3, "Dumping all objects")
        self.dump_objects(proc)

        # Shell
        self.update_progress(0.5, "Determining Python version")
        self.shell_buffer.set_text(
                proc.cmd('import sys; print("Python " + sys.version)'))

        # Dump stacks
        self.dump_stacks(proc)

        ## Call Stack
        self.generate_callgraph(proc)

        self.fontify()
        self.update_progress(1.0)
        self.update_progress(0.0)
        self.progress.hide()

    def dump_objects(self, proc):
        cmd = ';'.join(["import os, shutil", "from meliae import scanner",
                        "tmp = '/tmp/%d' % os.getpid()",
                        "scanner.dump_all_objects(tmp + '.json')",
                        "shutil.move(tmp + '.json', tmp + '.objects')"])
        proc.cmd(cmd)
        self.update_progress(0.35)

        # Clear previous model
        self.obj_store.clear()
        self.update_progress(0.4, "Loading object dump")

        obj_dump = '/tmp/%d.objects' % proc.pid
        if not os.path.exists(obj_dump):
            time.sleep(1)
            if not os.path.exists(obj_dump):
                time.sleep(2)

        objects = loader.load('/tmp/%d.objects' % proc.pid)
        objects.compute_referrers()
        self.update_progress(0.45)
        summary = objects.summarize()
        self.update_progress(0.47)

        def intify(x):
            try: return int(x)
            except: return x

        for i, line in enumerate(str(summary).split('\n')):
            if i == 0:
                self.obj_totals.set_text(line)
            elif i == 1:
                continue # column headers
            else:
                obj = summary.summaries[i - 2]
                self.obj_store.append([str(obj.max_address)] +
                                       map(intify, line.split()[1:]))
    def dump_stacks(self, proc):
        self.update_progress(0.55, "Dumping stacks")
        payloads = os.path.join(os.path.abspath(os.path.dirname(
            pyrasite.__file__)), '..', 'payloads')
        dump_stacks = os.path.join(payloads, 'dump_stacks.py')
        code = proc.cmd(file(dump_stacks).read())
        self.update_progress(0.6)

        start = self.source_buffer.get_iter_at_offset(0)
        end = start.copy()
        self.source_buffer.insert(end, code)

    def generate_callgraph(self, proc):
        self.update_progress(0.7, "Tracing call stack")
        proc.cmd('import pycallgraph; pycallgraph.start_trace()')
        self.update_progress(0.8)
        time.sleep(1)
        self.update_progress(0.9, "Generating call stack graph")
        image = '/tmp/%d-callgraph.png' % proc.pid
        proc.cmd('import pycallgraph; pycallgraph.make_dot_graph("%s")' % image)
        self.call_graph.set_from_file(image)

    def row_activated_cb(self, view, path, col, store):
        iter = store.get_iter(path)
        proc = store.get_value(iter, 1)
        if proc is not None:
            store.set_value(iter, 2, Pango.Style.NORMAL)

    def create_tree(self):
        tree_store = ProcessTreeStore()
        tree_view = Gtk.TreeView()
        self.tree_view = tree_view
        tree_view.set_model(tree_store)
        selection = tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.BROWSE)
        tree_view.set_size_request(200, -1)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(title = 'Processes',
                                    cell_renderer = cell,
                                    text = 0,
                                    style = 2)

        first_iter = tree_store.get_iter_first()
        if first_iter is not None:
            selection.select_iter(first_iter)

        selection.connect('changed', self.selection_cb, tree_store)
        tree_view.connect('row_activated', self.row_activated_cb, tree_store)

        tree_view.append_column(column)

        tree_view.collapse_all()
        tree_view.set_headers_visible(False)
        scrolled_window = Gtk.ScrolledWindow(hadjustment = None,
                                             vadjustment = None)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                   Gtk.PolicyType.AUTOMATIC)

        scrolled_window.add(tree_view)

        label = Gtk.Label(label = 'Processes')

        box = Gtk.Notebook()
        box.append_page(scrolled_window, label)

        tree_view.grab_focus()

        return box

    def create_text(self, is_source, return_view=False):
        scrolled_window = Gtk.ScrolledWindow(hadjustment = None,
                                             vadjustment = None)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                   Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_shadow_type(Gtk.ShadowType.IN)

        text_view = Gtk.TextView()
        buffer = Gtk.TextBuffer()

        text_view.set_buffer(buffer)
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)

        scrolled_window.add(text_view)

        if is_source:
            font_desc = Pango.FontDescription('monospace')
            text_view.modify_font(font_desc)
            text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        else:
            text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            text_view.set_pixels_above_lines(2)
            text_view.set_pixels_below_lines(2)

        if return_view:
            return (text_view, scrolled_window, buffer)
        return(scrolled_window, buffer)

    def fontify(self):
        start_iter = self.source_buffer.get_iter_at_offset(0)
        end_iter = self.source_buffer.get_iter_at_offset(0)
        data = self.source_buffer.get_text(self.source_buffer.get_start_iter(),
                                           self.source_buffer.get_end_iter(),
                                           False)

        if sys.version_info < (3, 0):
            data = data.decode('utf-8')

        builtin_constants = ['None', 'True', 'False']
        is_decorator = False
        is_func = False

        def prepare_iters():
            start_iter.set_line(srow-1)
            start_iter.set_line_offset(scol)
            end_iter.set_line(erow-1)
            end_iter.set_line_offset(ecol)

        for x in tokenize.generate_tokens(InputStream(data).readline):
            # x has 5-tuples
            tok_type, tok_str = x[0], x[1]
            srow, scol = x[2]
            erow, ecol = x[3]

            if tok_type == tokenize.COMMENT:
                prepare_iters()
                self.source_buffer.apply_tag_by_name('comment', start_iter, end_iter)
            elif tok_type == tokenize.NAME:
                if tok_str in keyword.kwlist or tok_str in builtin_constants:
                    prepare_iters()
                    self.source_buffer.apply_tag_by_name('keyword', start_iter, end_iter)

                    if tok_str == 'def' or tok_str == 'class':
                        # Next token is going to be a function/method/class name
                        is_func = True
                        continue
                elif tok_str == 'self':
                    prepare_iters()
                    self.source_buffer.apply_tag_by_name('italic', start_iter, end_iter)
                else:
                    if is_func is True:
                        prepare_iters()
                        self.source_buffer.apply_tag_by_name('bold', start_iter, end_iter)
                    elif is_decorator is True:
                        prepare_iters()
                        self.source_buffer.apply_tag_by_name('decorator', start_iter, end_iter)
            elif tok_type == tokenize.STRING:
                prepare_iters()
                self.source_buffer.apply_tag_by_name('string', start_iter, end_iter)
            elif tok_type == tokenize.NUMBER:
                prepare_iters()
                self.source_buffer.apply_tag_by_name('number', start_iter, end_iter)
            elif tok_type == tokenize.OP:
                if tok_str == '@':
                    prepare_iters()
                    self.source_buffer.apply_tag_by_name('decorator', start_iter, end_iter)

                    # next token is going to be the decorator name
                    is_decorator = True
                    continue

            if is_func is True:
                is_func = False

            if is_decorator is True:
                is_decorator = False

    def close(self):
        self.progress.show()
        self.update_progress(None, "Shutting down")
        print "Closing %r" % self
        for process in self.processes.values():
            self.update_progress(None)
            process.close()


def main():
    mainloop = GLib.MainLoop()

    window = PyrasiteWindow()
    window.show()

    def quit(widget, event, mainloop):
        window.close()
        mainloop.quit()

    window.connect('delete-event', quit, mainloop)

    try:
        mainloop.run()
    except KeyboardInterrupt:
        window.close()
        mainloop.quit()


if __name__ == '__main__':
    print "Loading Pyrasite..."
    main()

# vim: tabstop=4 shiftwidth=4 expandtab
