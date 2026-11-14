"""Smoke test: load the built gresource and construct the main window.

Run via `meson test`; APP_RESOURCE points at the built gresource.
"""

import os
import sys

SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCE = os.environ.get("APP_RESOURCE")

if not RESOURCE or not os.path.exists(RESOURCE):
    print("SKIP: APP_RESOURCE is not set")
    sys.exit(77)

sys.path.insert(0, SOURCE_ROOT)

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk

if not Gtk.init_check() or Gdk.Display.get_default() is None:
    print("SKIP: no display available")
    sys.exit(77)

Adw.init()

resource = Gio.Resource.load(RESOURCE)
resource._register()

from src.window import HelloWindow

window = HelloWindow()
assert "Hello" in window.get_title(), window.get_title()
window.destroy()
print("ok: window constructed")
