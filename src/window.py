# SPDX-License-Identifier: MIT

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/com/example/Hello/window.ui")
class HelloWindow(Adw.ApplicationWindow):
    __gtype_name__ = "HelloWindow"
