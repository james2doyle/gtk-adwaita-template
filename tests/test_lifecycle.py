"""In-process tests for application actions and window teardown."""

import gc
import os
import sys
import weakref

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
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

if not Gtk.init_check() or Gdk.Display.get_default() is None:
    print("SKIP: no display available")
    sys.exit(77)

Adw.init()

resource = Gio.Resource.load(RESOURCE)
resource._register()

from src.main import HelloApplication
from src.window import HelloWindow

app = HelloApplication("test")
app.register(None)

# Quit must request a window close rather than terminating immediately.
window = HelloWindow(application=app)
window.present()
while GLib.MainContext.default().iteration(False):
    pass
close_requests = []
window.connect(
    "close-request", lambda *_args: close_requests.append(True) or True
)
app.lookup_action("quit").activate()
assert close_requests == [True]
window.destroy()

# A destroyed window must not be retained by application or GTK signal state.
probe = HelloWindow(application=app)
reference = weakref.ref(probe)
probe.destroy()
probe.run_dispose()
while GLib.MainContext.default().iteration(False):
    pass
del probe
gc.collect()
gc.collect()
assert reference() is None, "destroyed window is still retained"

print("ok: application lifecycle")
