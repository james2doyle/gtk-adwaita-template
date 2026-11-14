# SPDX-License-Identifier: MIT

import logging
import os
import sys
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio

from .window import HelloWindow

log = logging.getLogger(__name__)


class HelloApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version):
        super().__init__(
            application_id="com.example.Hello",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/com/example/Hello",
        )
        self.version = version
        self.create_action("quit", lambda *_: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if necessary.
        """
        win = self.props.active_window
        if not win:
            win = HelloWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="Hello",
            application_icon="com.example.Hello",
            developer_name="James Doyle",
            version=self.version,
            # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
            translator_credits=_("translator-credits"),
            developers=["James Doyle"],
            copyright="© 2026 James Doyle",
        )
        about.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    configured_level = os.environ.get("G_MESSAGES_DEBUG", "")
    level = logging.DEBUG if configured_level else logging.INFO
    logging.basicConfig(level=level, format="%(name)s: %(message)s")
    log.info("Hello %s", version)
    app = HelloApplication(version)
    return app.run(sys.argv)
