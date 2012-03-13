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
#
# This interface may contain some code from the gtk-demo, written
# by John (J5) Palmieri, and licensed under the LGPLv2.1
# http://git.gnome.org/browse/pygobject/tree/demos/gtk-demo/gtk-demo.py

import os
import sys
import time
import socket
import psutil
import logging
import keyword
import tokenize
import threading

from os.path import join, abspath, dirname
from random import randrange
try:
    from meliae import loader
except:
    pass
from gi.repository import GLib, GObject, Pango, Gtk, WebKit

import pyrasite
from pyrasite.utils import setup_logger, run, humanize_bytes

log = logging.getLogger('pyrasite')

POLL_INTERVAL = 1.0
INTERVALS = 200
cpu_intervals = []
cpu_details = ''
mem_intervals = []
mem_details = ''
write_intervals = []
read_intervals = []
read_count = read_bytes = write_count = write_bytes = 0

thread_intervals = {}
thread_colors = {}
thread_totals = {}

open_connections = []
open_files = []

# Prefer tango colors for our lines. Fall back to random ones.
tango = ['c4a000', 'ce5c00', '8f5902', '4e9a06', '204a87', '5c3566',
         'a40000', '555753']


def get_color():
    used = thread_colors.values()
    for color in tango:
        if color not in used:
            return color
    return "".join([hex(randrange(0, 255))[2:] for i in range(3)])


class Process(pyrasite.PyrasiteIPC, GObject.GObject):
    """
    A :class:`GObject.GObject` subclass that represents a Process, for use in
    the :class:`ProcessTreeStore`
    """

    @property
    def title(self):
        if not getattr(self, '_title', None):
            self._title = run('ps --no-heading -o cmd= -p %d' % self.pid)[1] \
                    .decode('utf-8')
        return self._title


class ProcessListStore(Gtk.ListStore):
    """This TreeStore finds all running python processes."""

    def __init__(self, *args):
        Gtk.ListStore.__init__(self, str, Process, Pango.Style)
        for pid in os.listdir('/proc'):
            try:
                pid = int(pid)
                proc = Process(pid)
                try:
                    maps = open('/proc/%d/maps' % pid).read().strip()
                    if 'python' in maps:
                        self.append((proc.title.strip(), proc,
                                     Pango.Style.NORMAL))
                except IOError:
                    pass
            except ValueError:
                pass


class PyrasiteWindow(Gtk.Window):

    def __init__(self):
        super(PyrasiteWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)

        self.processes = {}
        self.pid = None  # Currently selected pid
        self.resource_thread = None

        self.set_title('Pyrasite v%s' % pyrasite.__version__)
        self.set_default_size(600, 400)

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

        self.info_html = ''
        self.info_view = WebKit.WebView()
        self.info_view.load_string(self.info_html, "text/html", "utf-8", '#')

        info_window = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        info_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                               Gtk.PolicyType.AUTOMATIC)
        info_window.add(self.info_view)
        notebook.append_page(info_window,
                Gtk.Label.new_with_mnemonic('_Resources'))

        (stacks_widget, source_buffer) = self.create_text(True)
        notebook.append_page(stacks_widget,
                Gtk.Label.new_with_mnemonic('_Stacks'))

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
            Gtk.TreeViewColumn(title='Count',
                               cell_renderer=Gtk.CellRendererText(),
                               text=1, style=2),
            Gtk.TreeViewColumn(title='%',
                               cell_renderer=Gtk.CellRendererText(),
                               text=2, style=2),
            Gtk.TreeViewColumn(title='Size',
                               cell_renderer=Gtk.CellRendererText(),
                               text=3, style=2),
            Gtk.TreeViewColumn(title='%',
                               cell_renderer=Gtk.CellRendererText(),
                               text=4, style=2),
            Gtk.TreeViewColumn(title='Cumulative',
                               cell_renderer=Gtk.CellRendererText(),
                               text=5, style=2),
            Gtk.TreeViewColumn(title='Max',
                               cell_renderer=Gtk.CellRendererText(),
                               text=6, style=2),
            Gtk.TreeViewColumn(title='Kind',
                               cell_renderer=Gtk.CellRendererText(),
                               text=7, style=2),
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

        scrolled_window = Gtk.ScrolledWindow(hadjustment=None,
                                             vadjustment=None)
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

        (shell_view, shell_widget, shell_buffer) = \
                self.create_text(False, return_view=True)
        self.shell_view = shell_view
        self.shell_buffer = shell_buffer
        self.shell_widget = shell_widget
        shell_hbox = Gtk.VBox()
        shell_hbox.pack_start(shell_widget, True, True, 0)
        shell_bottom = Gtk.HBox()

        shell_prompt = Gtk.Entry()
        self.shell_prompt = shell_prompt
        self.shell_prompt.connect('activate', self.run_shell_command)
        shell_bottom.pack_start(shell_prompt, True, True, 0)

        self.shell_button = shell_button = Gtk.Button('Run')
        shell_button.connect('clicked', self.run_shell_command)
        shell_bottom.pack_start(shell_button, False, False, 0)
        shell_hbox.pack_end(shell_bottom, False, False, 0)

        shell_label = Gtk.Label.new_with_mnemonic('_Shell')
        notebook.append_page(shell_hbox, shell_label)

        # To try and grab focus of our text input
        notebook.connect('switch-page', self.switch_page)
        self.notebook = notebook

        self.call_graph = Gtk.Image()
        scrolled_window = Gtk.ScrolledWindow(hadjustment=None,
                                             vadjustment=None)
        scrolled_window.set_policy(Gtk.PolicyType.ALWAYS,
                                   Gtk.PolicyType.ALWAYS)

        scrolled_window.add_with_viewport(self.call_graph)

        notebook.append_page(scrolled_window,
                Gtk.Label.new_with_mnemonic('_Call Graph'))

        self.details_html = ''
        self.details_view = WebKit.WebView()
        self.details_view.load_string(self.details_html, "text/html",
                                      "utf-8", '#')

        details_window = Gtk.ScrolledWindow(hadjustment=None,
                                            vadjustment=None)
        details_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                               Gtk.PolicyType.AUTOMATIC)
        details_window.add(self.details_view)
        notebook.append_page(details_window,
                Gtk.Label.new_with_mnemonic('_Details'))

        self.show_all()
        self.progress.hide()

    def switch_page(self, notebook, page, pagenum):
        name = self.notebook.get_tab_label(self.notebook.get_nth_page(pagenum))
        if name.get_text() == 'Shell':
            GObject.timeout_add(0, self.shell_prompt.grab_focus)

    def run_shell_command(self, widget):
        cmd = self.shell_prompt.get_text()
        end = self.shell_buffer.get_end_iter()
        self.shell_buffer.insert(end, '\n>>> %s\n' % cmd)
        log.debug("run_shell_command(%r)" % cmd)
        output = self.proc.cmd(cmd)
        log.debug(repr(output))
        self.shell_buffer.insert(end, output)
        self.shell_prompt.set_text('')

        insert_mark = self.shell_buffer.get_insert()
        self.shell_buffer.place_cursor(self.shell_buffer.get_end_iter())
        self.shell_view.scroll_to_mark(insert_mark, 0.0, True, 0.0, 1.0)

    def obj_selection_cb(self, selection, model):
        sel = selection.get_selected()
        treeiter = sel[1]
        addy = model.get_value(treeiter, 0)
        inspector = pyrasite.ObjectInspector(self.pid)
        value = inspector.inspect(addy)
        if value:
            self.obj_buffer.set_text(value)
        else:
            self.obj_buffer.set_text('Unable to inspect object. Make sure you '
                    'have the python debugging symbols installed.')

    def obj_row_activated_cb(self, *args, **kw):
        log.debug("obj_row_activated_cb(%s, %s)" % (args, kw))

    def generate_description(self, proc, title):
        p = psutil.Process(proc.pid)

        self.info_html = """
        <html><head>
            <style>
            body {font: normal 12px/150%% Arial, Helvetica, sans-serif;}
            .grid table {
                border-collapse: collapse;
                text-align: left;
                width: 100%%;
            }
            .grid {
                font: normal 12px/150%% Arial, Helvetica, sans-serif;
                background: #fff; overflow: hidden; border: 1px solid #2e3436;
                -webkit-border-radius: 3px; border-radius: 3px;
            }
            .grid table td, .grid table th { padding: 3px 10px; }
            .grid table thead th {
                background:-webkit-gradient(linear, left top, left bottom,
                                            color-stop(0.05, #888a85),
                                            color-stop(1, #555753) );
                background-color:#2e3436; color:#FFFFFF; font-size: 15px;
                font-weight: bold; border-left: 1px solid #2e3436; }
            .grid table thead th:first-child { border: none; }
            .grid table tbody td {
                color: #2e3436;
                border-left: 1px solid #2e3436;
                font-size: 12px;
                font-weight: normal;
            }
            .grid table tbody .alt td { background: #d3d7cf; color: #2e3436; }
            .grid table tbody td:first-child { border: none; }
            </style>
        </head>
        <body>
            <h2>%(title)s</h2>
                <div class="grid">
                <table>
                    <thead><tr>
                        <th width="50%%">CPU: <span id="cpu_details"/></th>
                        <th width="50%%">Memory: <span id="mem_details"/></th>
                    </tr></thead>
                    <tbody>
                        <tr>
                            <td>
                                <span id="cpu_graph" class="cpu_graph"></span>
                            </td>
                            <td>
                                <span id="mem_graph" class="mem_graph"></span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <br/>
            <div class="grid">
                <table>
                    <thead><tr>
                        <th width="50%%">Read: <span id="read_details"/></th>
                        <th width="50%%">Write: <span id="write_details"/></th>
                    </tr></thead>
                    <tbody>
                        <tr><td><span id="read_graph"></span></td>
                            <td><span id="write_graph"></span></td></tr>
                    </tbody>
                </table>
            </div>
            <br/>
            <div class="grid">
                <table>
                    <thead>
                        <tr><th>Threads</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><span id="thread_graph"></span></td></tr>
                    </tbody>
                </table>
            </div>
            <br/>
        """ % dict(title=proc.title)

        self.info_html += """
        <div class="grid">
            <table>
                <thead><tr><th>Open Files</th></tr></thead>
                <tbody id="open_files"></tbody>
            </table>
        </div>
        <br/>
        <div class="grid">
            <table>
                <thead><tr><th colspan="4">Connections</th></tr></thead>
                <tbody id="open_connections"></tbody>
            </table>
        </div>
        </body></html>
        """

        self.info_view.load_string(self.info_html, "text/html", "utf-8", '#')

        # The Details tab
        self.details_html = """
        <style>
        body {font: normal 12px/150%% Arial, Helvetica, sans-serif;}
        </style>
        <h2>%s</h2>
        <ul>
            <li><b>status:</b> %s</li>
            <li><b>cwd:</b> %s</li>
            <li><b>cmdline:</b> %s</li>
            <li><b>terminal:</b> %s</li>
            <li><b>created:</b> %s</li>
            <li><b>username:</b> %s</li>
            <li><b>uid:</b> %s</li>
            <li><b>gid:</b> %s</li>
            <li><b>nice:</b> %s</li>
        </ul>
        """ % (proc.title, p.status, p.getcwd(), ' '.join(p.cmdline),
               getattr(p, 'terminal', 'unknown'), time.ctime(p.create_time),
               p.username, p.uids.real, p.gids.real, p.nice)

        self.details_view.load_string(self.details_html, "text/html",
                                      "utf-8", '#')

        if not self.resource_thread:
            self.resource_thread = ResourceUsagePoller(proc.pid)
            #self.resource_thread.process = p
            self.resource_thread.daemon = True
            self.resource_thread.info_view = self.info_view
            self.resource_thread.start()
        self.resource_thread.process = p

        GObject.timeout_add(100, self.inject_js)
        GObject.timeout_add(int(POLL_INTERVAL * 1000),
                            self.render_resource_usage)

    def inject_js(self):
        log.debug("Injecting jQuery")
        js = join(dirname(abspath(__file__)), 'js')
        jquery = open(join(js, 'jquery-1.7.1.min.js'))
        self.info_view.execute_script(jquery.read())
        jquery.close()
        sparkline = open(join(js, 'jquery.sparkline.min.js'))
        self.info_view.execute_script(sparkline.read())
        sparkline.close()

    def render_resource_usage(self):
        """
        Render our resource usage using jQuery+Sparklines in our WebKit view
        """
        global cpu_intervals, mem_intervals, cpu_details, mem_details
        global read_intervals, write_intervals, read_bytes, write_bytes
        global open_files, open_connections
        script = """
            jQuery('#cpu_graph').sparkline(%s, {'height': 75, 'width': 250,
                spotRadius: 3, fillColor: '#73d216', lineColor: '#4e9a06'});
            jQuery('#mem_graph').sparkline(%s, {'height': 75, 'width': 250,
                lineColor: '#5c3566', fillColor: '#75507b',
                minSpotColor: false, maxSpotColor: false, spotColor: '#f57900',
                spotRadius: 3});
            jQuery('#cpu_details').text('%s');
            jQuery('#mem_details').text('%s');
            jQuery('#read_graph').sparkline(%s, {'height': 75, 'width': 250,
                lineColor: '#a40000', fillColor: '#cc0000',
                minSpotColor: false, maxSpotColor: false, spotColor: '#729fcf',
                spotRadius: 3});
            jQuery('#write_graph').sparkline(%s, {'height': 75, 'width': 250,
                lineColor: '#ce5c00', fillColor: '#f57900',
                minSpotColor: false, maxSpotColor: false, spotColor: '#8ae234',
                spotRadius: 3});
            jQuery('#read_details').text('%s');
            jQuery('#write_details').text('%s');
        """ % (cpu_intervals, mem_intervals, cpu_details, mem_details,
               read_intervals, write_intervals, humanize_bytes(read_bytes),
               humanize_bytes(write_bytes))

        for i, thread in enumerate(thread_intervals):
            script += """
                jQuery('#thread_graph').sparkline(%s, {
                    %s'lineColor': '#%s', 'fillColor': false, 'spotRadius': 3,
                    'spotColor': '#%s'});
            """ % (thread_intervals[thread], i != 0 and "'composite': true,"
                   or "'height': 75, 'width': 575,", thread_colors[thread],
                   thread_colors[thread])

        if open_files:
            script += """
                jQuery('#open_files').html('%s');
            """ % ''.join(['<tr%s><td>%s</td></tr>' %
                           (i % 2 and ' class="alt"' or '', open_file)
                           for i, open_file in enumerate(open_files)])

        if open_connections:
            row = '<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
            script += """
                jQuery('#open_connections').html('%s');
            """ % ''.join([row % (i % 2 and ' class="alt"' or '',
                                  conn['type'], conn['local'],
                                  conn['remote'], conn['status'])
                           for i, conn in enumerate(open_connections)])

        self.info_view.execute_script(script)
        return True

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

        if self.pid and proc.pid != self.pid:
            global cpu_intervals, mem_intervals, write_intervals, \
                   read_intervals, cpu_details, mem_details, read_count, \
                   read_bytes, thread_totals, write_count, write_bytes, \
                   thread_intervals, thread_colors, open_files, \
                   open_connections
            cpu_intervals = [0.0]
            mem_intervals = []
            write_intervals = []
            read_intervals = []
            cpu_details = mem_details = ''
            read_count = read_bytes = write_count = write_bytes = 0
            thread_intervals = {}
            thread_colors = {}
            thread_totals = {}
            open_connections = []
            open_files = []

        self.pid = proc.pid

        # Analyze the process
        self.generate_description(proc, title)

        # Inject a reverse subshell
        self.update_progress(0.2, "Injecting reverse connection")
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
        self.progress.hide()
        self.update_progress(0.0)

    def dump_objects(self, proc):
        cmd = ';'.join(["import os, shutil", "from meliae import scanner",
                        "tmp = '/tmp/%d' % os.getpid()",
                        "scanner.dump_all_objects(tmp + '.json')",
                        "shutil.move(tmp + '.json', tmp + '.objects')"])
        output = proc.cmd(cmd)
        if 'No module named meliae' in output:
            log.error('Error: %s is unable to import `meliae`' %
                      proc.title.strip())
            return
        self.update_progress(0.35)

        # Clear previous model
        self.obj_store.clear()
        self.update_progress(0.4, "Loading object dump")

        try:
            objects = loader.load('/tmp/%d.objects' % proc.pid,
                                  show_prog=False)
        except NameError:
            log.debug("Meliae not available, continuing...")
            return
        except:
            log.debug("Falling back to slower meliae object dump loader")
            objects = loader.load('/tmp/%d.objects' % proc.pid,
                                  show_prog=False, using_json=False)
        objects.compute_referrers()
        self.update_progress(0.45)
        summary = objects.summarize()
        self.update_progress(0.47)

        def intify(x):
            try:
                return int(x)
            except:
                return x

        for i, line in enumerate(str(summary).split('\n')):
            if i == 0:
                self.obj_totals.set_text(line)
            elif i == 1:
                continue  # column headers
            else:
                obj = summary.summaries[i - 2]
                self.obj_store.append([str(obj.max_address)] +
                                       map(intify, line.split()[1:]))

        os.unlink('/tmp/%d.objects' % proc.pid)

    def dump_stacks(self, proc):
        self.update_progress(0.55, "Dumping stacks")
        payloads = os.path.join(os.path.abspath(os.path.dirname(
            pyrasite.__file__)), 'payloads')
        dump_stacks = os.path.join(payloads, 'dump_stacks.py')
        code = proc.cmd(open(dump_stacks).read())
        self.update_progress(0.6)

        self.source_buffer.set_text('')
        start = self.source_buffer.get_iter_at_offset(0)
        end = start.copy()
        self.source_buffer.insert(end, code)

    def generate_callgraph(self, proc):
        self.update_progress(0.7, "Tracing call stack")
        proc.cmd('import pycallgraph; pycallgraph.start_trace()')
        self.update_progress(0.8)
        time.sleep(1)  # TODO: make this configurable in the UI
        self.update_progress(0.9, "Generating call stack graph")
        image = '/tmp/%d-callgraph.png' % proc.pid
        proc.cmd('import pycallgraph; pycallgraph.make_dot_graph("%s")' %
                 image)
        self.call_graph.set_from_file(image)

    def row_activated_cb(self, view, path, col, store):
        iter = store.get_iter(path)
        proc = store.get_value(iter, 1)
        if proc is not None:
            store.set_value(iter, 2, Pango.Style.NORMAL)

    def create_tree(self):
        tree_store = ProcessListStore()
        tree_view = Gtk.TreeView()
        self.tree_view = tree_view
        tree_view.set_model(tree_store)
        selection = tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.BROWSE)
        tree_view.set_size_request(200, -1)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(title='Processes', cell_renderer=cell,
                                    text=0, style=2)

        first_iter = tree_store.get_iter_first()
        if first_iter is not None:
            selection.select_iter(first_iter)

        selection.connect('changed', self.selection_cb, tree_store)
        tree_view.connect('row_activated', self.row_activated_cb, tree_store)

        tree_view.append_column(column)

        tree_view.collapse_all()
        tree_view.set_headers_visible(False)
        scrolled_window = Gtk.ScrolledWindow(hadjustment=None,
                                             vadjustment=None)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                   Gtk.PolicyType.AUTOMATIC)

        scrolled_window.add(tree_view)

        label = Gtk.Label(label='Processes')

        box = Gtk.Notebook()
        box.set_size_request(250, -1)
        box.append_page(scrolled_window, label)

        tree_view.grab_focus()

        return box

    def create_text(self, is_source, return_view=False):
        scrolled_window = Gtk.ScrolledWindow(hadjustment=None,
                                             vadjustment=None)
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
            start_iter.set_line(srow - 1)
            start_iter.set_line_offset(scol)
            end_iter.set_line(erow - 1)
            end_iter.set_line_offset(ecol)

        try:
            for x in tokenize.generate_tokens(InputStream(data).readline):
                # x has 5-tuples
                tok_type, tok_str = x[0], x[1]
                srow, scol = x[2]
                erow, ecol = x[3]

                if tok_type == tokenize.COMMENT:
                    prepare_iters()
                    self.source_buffer.apply_tag_by_name('comment', start_iter,
                                                         end_iter)
                elif tok_type == tokenize.NAME:
                    if (tok_str in keyword.kwlist or
                        tok_str in builtin_constants):
                        prepare_iters()
                        self.source_buffer.apply_tag_by_name('keyword',
                                                             start_iter,
                                                             end_iter)
                        if tok_str == 'def' or tok_str == 'class':
                            # Next token is going to be a
                            # function/method/class name
                            is_func = True
                            continue
                    elif tok_str == 'self':
                        prepare_iters()
                        self.source_buffer.apply_tag_by_name('italic',
                                                             start_iter,
                                                             end_iter)
                    else:
                        if is_func is True:
                            prepare_iters()
                            self.source_buffer.apply_tag_by_name('bold',
                                                                 start_iter,
                                                                 end_iter)
                        elif is_decorator is True:
                            prepare_iters()
                            self.source_buffer.apply_tag_by_name('decorator',
                                                                 start_iter,
                                                                 end_iter)
                elif tok_type == tokenize.STRING:
                    prepare_iters()
                    self.source_buffer.apply_tag_by_name('string', start_iter,
                                                         end_iter)
                elif tok_type == tokenize.NUMBER:
                    prepare_iters()
                    self.source_buffer.apply_tag_by_name('number', start_iter,
                                                         end_iter)
                elif tok_type == tokenize.OP:
                    if tok_str == '@':
                        prepare_iters()
                        self.source_buffer.apply_tag_by_name('decorator',
                                                             start_iter,
                                                             end_iter)

                        # next token is going to be the decorator name
                        is_decorator = True
                        continue

                if is_func is True:
                    is_func = False

                if is_decorator is True:
                    is_decorator = False
        except tokenize.TokenError:
            pass

    def close(self):
        self.progress.show()
        self.update_progress(None, "Shutting down")
        log.debug("Closing %r" % self)
        for process in self.processes.values():
            self.update_progress(None)
            process.close()
            callgraph = '/tmp/%d-callgraph.png' % process.pid
            if os.path.exists(callgraph):
                os.unlink(callgraph)


class InputStream(object):
    '''
    Simple Wrapper for File-like objects. [c]StringIO doesn't provide
    a readline function for use with generate_tokens.
    Using a iterator-like interface doesn't succeed, because the readline
    function isn't used in such a context. (see <python-lib>/tokenize.py)
    '''
    def __init__(self, data):
        self.__data = ['%s\n' % x for x in data.splitlines()]
        self.__lcount = 0

    def readline(self):
        try:
            line = self.__data[self.__lcount]
            self.__lcount += 1
        except IndexError:
            line = ''
            self.__lcount = 0

        return line


class ResourceUsagePoller(threading.Thread):
    """A thread for polling a processes CPU & memory usage"""
    process = None

    def __init__(self, pid):
        super(ResourceUsagePoller, self).__init__()
        self.process = psutil.Process(pid)

    def run(self):
        global cpu_intervals, mem_intervals, cpu_details, mem_details
        global read_count, read_bytes, write_count, write_bytes
        global read_intervals, write_intervals, thread_intervals
        global open_files, open_connections
        while True:
            if self.process:
                if len(cpu_intervals) >= INTERVALS:
                    cpu_intervals = cpu_intervals[1:INTERVALS]
                    mem_intervals = mem_intervals[1:INTERVALS]
                    read_intervals = read_intervals[1:INTERVALS]
                    write_intervals = write_intervals[1:INTERVALS]

                cpu_intervals.append(
                    self.process.get_cpu_percent(interval=POLL_INTERVAL))
                mem_intervals.append(self.process.get_memory_info().rss)
                cputimes = self.process.get_cpu_times()
                cpu_details = '%0.2f%% (%s user, %s system)' % (
                        cpu_intervals[-1], cputimes.user, cputimes.system)
                meminfo = self.process.get_memory_info()
                mem_details = '%0.2f%% (%s RSS, %s VMS)' % (
                        self.process.get_memory_percent(),
                        humanize_bytes(meminfo.rss),
                        humanize_bytes(cputimes.system))

                io = self.process.get_io_counters()
                read_since_last = io.read_bytes - read_bytes
                read_intervals.append(read_since_last)
                read_count = io.read_count
                read_bytes = io.read_bytes
                write_since_last = io.write_bytes - write_bytes
                write_intervals.append(write_since_last)
                write_count = io.write_count
                write_bytes = io.write_bytes

                for thread in self.process.get_threads():
                    if thread.id not in thread_intervals:
                        thread_intervals[thread.id] = []
                        thread_colors[thread.id] = get_color()
                        thread_totals[thread.id] = 0.0

                    if len(thread_intervals[thread.id]) >= INTERVALS:
                        thread_intervals[thread.id] = \
                                thread_intervals[thread.id][1:INTERVALS]

                    # FIXME: we should figure out some way to visually
                    # distinguish between user and system time.
                    total = thread.system_time + thread.user_time
                    amount_since = total - thread_totals[thread.id]
                    thread_intervals[thread.id].append(
                            float('%.2f' % amount_since))
                    thread_totals[thread.id] = total

            # Open connections
            connections = []
            for i, conn in enumerate(self.process.get_connections()):
                if conn.type == socket.SOCK_STREAM:
                    type = 'TCP'
                elif conn.type == socket.SOCK_DGRAM:
                    type = 'UDP'
                else:
                    type = 'UNIX'
                lip, lport = conn.local_address
                if not conn.remote_address:
                    rip = rport = '*'
                else:
                    rip, rport = conn.remote_address
                connections.append({
                    'type': type,
                    'status': conn.status,
                    'local': '%s:%s' % (lip, lport),
                    'remote': '%s:%s' % (rip, rport),
                    })
            open_connections = connections

            # Open files
            files = []
            for open_file in self.process.get_open_files():
                files.append(open_file.path)
            open_files = files


def main():
    GObject.threads_init()
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
    setup_logger(verbose='-v' in sys.argv)
    log.info("Loading Pyrasite...")
    sys.exit(main())

# vim: tabstop=4 shiftwidth=4 expandtab
