# AGENTS.md — Hello

GTK 4 + libadwaita application in Python 3 (PyGObject), with Blueprint UI
(`.blp` compiles to GtkBuilder XML at build time), Meson, gettext i18n and
Flatpak packaging. App ID: `com.example.Hello`. Minimum libadwaita is 1.8
(the scaffold targets 1.10 in the GNOME 51 runtime).

IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning for
GTK4/libadwaita/Blueprint tasks.

## Finding documentation

- GTK: https://docs.gtk.org/gtk4/
- GTK search: https://docs.gtk.org/gtk4/?q=%s
- libadwaita: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/index.html?q=%s
- libadwaita stylesheet: https://github.com/GNOME/libadwaita/tree/1.10.0/src/stylesheet

## Build & verify

```sh
meson setup build --prefix="$PWD/build-install"  # once
meson compile -C build
python3 scripts/test.py
meson install -C build
./build-install/bin/hello
blueprint-compiler compile src/window.blp
blueprint-compiler lint src/window.blp
sh -n scripts/build-appimage.sh
uvx pyright src tests scripts dev.py
uvx ruff check --select E9,F63,F7,F82,F401,I001 src tests scripts dev.py
```

Definition of done for a change: `blueprint-compiler compile` on touched
`.blp` files, `python3 scripts/test.py` green, full `meson compile -C build`,
and the app launches via `./build-install/bin/hello`. Lint each touched `.blp`
file as the final step. When `uv` is available, keep pyright and that ruff
selection clean. If the AppImage script or recipe changes, run
`sh -n scripts/build-appimage.sh`; the full container build runs in the release
workflow. The test wrapper removes stale logs and runs Meson with an
allow-listed environment so credentials are not copied into
`build/meson-logs`.

`dev.py` rebuilds and relaunches on save:

```sh
python3 dev.py
```

## Debugging

**Rule: prefer a test in `tests/` over driving the running UI.** Add a
headless test for logic, or an in-process widget test that inspects the real
GTK widget tree. Never drive the GUI, move the pointer, type, or send
shortcuts without explicit permission for that run. When a visual check is
necessary, ask first and use the desktop automation tool the user has
approved. Do not build verification around xdotool or ydotool.

Tips:

- Run `python3 scripts/test.py`; add `--verbose` when debugging one test.
  Headless tests can also be run directly with `python3 tests/test_foo.py`
  while iterating.
- GUI tests must call `Gtk.init_check()` and exit 77 when no display is
  available. Never construct GTK widgets in a no-display process.
- Keep logic in modules that do not import GTK, so it can be tested headlessly.
  For asynchronous GIO work, run a `GLib.MainLoop` in the test.
- `G_DEBUG=fatal-criticals timeout 5 ./build-install/bin/hello` turns GTK
  criticals into failures; the timeout is needed because GUI apps stay open.
- `GTK_DEBUG=interactive ./build-install/bin/hello` opens the GTK Inspector.
- If launching appears to do nothing, check for an already-running instance:
  `Adw.Application` is single-instance and forwards activation to it.
- Under X11/Xwayland, ibus can segfault in `gdk_x11_surface_get_xid`. Set
  `GTK_IM_MODULE=gtk-im-context-simple` for X11 runs.
- Prefer a test over automation. If a visual check is approved, use a tool that
  works on the user's session; Wayland and X11 expose different capabilities,
  and unapproved automation is hard to reproduce.
- Ask before taking screenshots. GNOME Shell's screenshot D-Bus may be denied;
  under Xwayland, capture a specific window with ImageMagick
  `import -window <id>` after the user approves.
- If a rebuilt UI change seems ignored, run `ninja -C build -d explain` and
  verify the generated `build/src/*.ui` file.
- `G_MESSAGES_DEBUG=all` controls GLib log domains and can produce enormous
  output. Use `HELLO_DEBUG=1` for the app's Python `DEBUG` logging, or the GTK
  Inspector when diagnosing a specific widget.

## Hard boundaries

- Don't edit generated `.ui` files — Meson runs `blueprint-compiler compile`
  for each `.blp` and writes them to `build/src/*.ui` (see `src/meson.build`).
- Don't leave user-visible strings unwrapped. Wrap them in `_(...)` in
  `.py`/`.blp` and add the file to `po/POTFILES.in`.
- Don't import gi repositories unguarded. Call `gi.require_version` first
  (`Gtk` `4.0`, `Adw` `1`, and any other repository).
- Prefer Adwaita style classes in `styles [...]` blocks. Scoped app CSS is
  allowed for custom content widgets (for example a Markdown preview, code
  blocks, tables or alerts); add `style.css` to the GResource base path and let
  `Adw.Application` load it. Load CSS manually only for a plain
  `Gtk.Application` or a runtime-generated provider.
- Keep `src/hello.in` APPDIR-aware. The AppImage resolves `pkgdatadir` and
  `localedir` under `$APPDIR/usr/share`; a launcher that only uses the
  configured prefix loads host resources instead of the bundled ones.
- Don't ship a read-only install without bytecode. `scripts/compile-bytecode.py`
  runs from `meson install`; keep that wiring.
- Don't read/write settings ad hoc. Add the key to
  `data/com.example.Hello.gschema.xml` first, then use `Gio.Settings`.
- Don't persist app data ad hoc. Add a dedicated storage module with explicit
  schema/versioning if the app needs persistence.
- Keep Meson source/file lists explicit — no globbing.
- Never commit environment files, private keys, tokens, credentials, or test
  logs containing the caller's environment. Use `scripts/test.py` rather than
  invoking `meson test` from a shell that may contain secrets.

## UI logic placement

| Concern | Blueprint (`.blp`) | Python |
| :--- | :---: | :---: |
| Static layout, labels, style classes, menus | Yes | |
| Property bindings between widgets | Yes (`bind`/`as`/`bidirectional`) | |
| Breakpoints / adaptive shells | Yes (`setters`) | |
| Anything that changes at runtime | | Yes |
| Signal handlers, actions, dialog flow | | Yes |

Configure appearance and state in Blueprint; code wires behavior. Only set in
code what changes at runtime.

## Startup performance

The first frame is part of the UI. Build the window, present it, then defer
work that is not needed for the first paint:

- Lazy-import window and content modules. `src/main.py` imports the window in
  `do_activate`, not at application-module import time; `tests/test_startup.py`
  guards that boundary in a fresh subprocess.
- Defer syntax highlighting, spell-check setup, and large preview/parser trees
  to `GLib.PRIORITY_LOW` idles. Guard callbacks with a destroyed-window check.
- Keep `__init__` limited to layout, signals, and cheap state.
- Ship bytecode. `scripts/compile-bytecode.py` runs at install time so
  read-only Flatpak and AppImage installs do not recompile on every launch.
- Measure before optimizing: `PYTHONPROFILEIMPORTTIME=1`, `GDK_DEBUG=frames`,
  py-spy, and Sysprof. Display tests that assert deferred state must drain
  `GLib.MainContext` first.

## Workflow: new window or dialog

1. Create `src/foo.blp`. Base it on the skeleton in
   `.agents/skills/gtk-guidelines/SKILL.md`.
2. Add `foo` to the blueprint name list in `src/meson.build`; the foreach
   generates `build/src/foo.ui`.
3. Add `<file preprocess="xml-stripblanks">foo.ui</file>` to
   `src/hello.gresource.xml`.
4. Create the Python class with one `Gtk.Template.Child()` per widget ID you
   reference from code.
5. If another `.blp` uses the template (`$HelloFoo`), import its class in that
   module so the GType is registered before the builder runs
   (`from .foo import HelloFoo  # noqa: F401`).
6. If it opens from the app, wire an action (next workflow).
7. Verify: compile and lint, run, present it.

## Workflow: new action

1. In `HelloApplication.__init__`:
   `self.create_action('name', self.on_name_action, ['<control>n'])`.
2. Wire it from `.blp`: a menu item
   (`item { label: _("_Name"); action: "app.name"; }`) or a control
   (`action-name: "app.name";` on a Button/ToggleButton).
3. In the callback, build the dialog and
   `.present(self.props.active_window)`.
4. Add the shortcut to `src/shortcuts-dialog.blp` if keyboard-accessible.
5. Verify the action string is exactly `"app." + name`.

`app.shortcuts` needs no `create_action`: `Adw.Application` loads
`shortcuts-dialog.ui` (an `Adw.ShortcutsDialog` with ID `shortcuts_dialog`)
and registers the action + `Ctrl-?` itself.

Window-scoped actions use the `win.` prefix and are registered on the window
itself. A plain `Adw.Window` does not implement `Gio.ActionMap`; insert a
`Gio.SimpleActionGroup` with `self.insert_action_group("win", group)`.

## Snippets

Register an application action:

```python
def create_action(self, name, callback, shortcuts=None):
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", callback)
    self.add_action(action)
    if shortcuts:
        self.set_accels_for_action(f"app.{name}", shortcuts)
```

Composite-template window class:

```python
@Gtk.Template(resource_path='/com/example/Hello/foo.ui')
class HelloFoo(Adw.Bin):
    __gtype_name__ = 'HelloFoo'

    label = Gtk.Template.Child()
```

GSettings access (add the key to the gschema first):

```python
settings = Gio.Settings(schema_id='com.example.Hello')
settings.bind('key-name', widget, 'active', Gio.SettingsBindFlags.DEFAULT)
```

The installed launcher adds its prefix to `GSETTINGS_SCHEMA_DIR` and
`XDG_DATA_DIRS`, so schemas and icons also resolve from `build-install`.

## Async operation ownership

The scaffold has no file or network I/O. When adding it, treat every async
callback as untrusted with respect to the current UI state:

- Capture an immutable payload and an operation/document generation before
  starting the work. On completion, discard the result if either changed.
- Serialize writes to the same file. A later save must not be overwritten by
  an older completion.
- Mark a document saved against the payload that was written, never against
  the buffer's current text. Otherwise edits made during the write are
  incorrectly reported clean and can be lost on close.
- Cancel loads on New/Open/close, and cancel or invalidate preview, image, and
  network work when its document or window is destroyed.
- Disconnect long-lived global signals (settings, style managers) in the
  destroy handler, and add an in-process lifecycle test for teardown.
- Apply explicit byte, count, and time limits at the I/O boundary. Do not rely
  on callback ordering, cancellation, or a timeout alone for resource safety.

See the payload-lifetime gotcha below as well.

## Optional integrations

### GtkSourceView

The template does not depend on GtkSourceView. If you add a `GtkSource.View`
to a Blueprint file, install the typelib and register the GType before
GtkBuilder parses the template:

```python
gi.require_version("GtkSource", "5")
from gi.repository import GtkSource

# PyGObject registers namespace types lazily; GtkBuilder needs the GType
# before Gtk.Template builds a template containing GtkSourceView. Call this
# from the window's __init__ before super().__init__() (or from application
# startup after GTK is initialized).
GtkSource.View()
```

Add `gtksourceview5` to the CI `dnf install` list. The GNOME Flatpak runtime
ships GtkSourceView 5; if you target another runtime, add the GtkSourceView
module to the manifest as well.

### Vendored Python packages

Install pure-Python dependencies with `install_subdir()` rather than listing
every file, and exclude bytecode caches:

```meson
install_subdir('vendor',
  install_dir: moduledir,
  exclude_directories: ['**/__pycache__'],
  exclude_files: ['**/*.pyc'],
)
```

Both exclusions are needed: depending on the Meson version, excluding the
cache directories alone can still install generated bytecode. Add the vendor
directory to `sys.path` before importing the package.

### Install-time bytecode

`src/meson.build` runs `scripts/compile-bytecode.py` after installing the
Python sources. Flatpak and AppImage installs are read-only, so without shipped
bytecode Python recompiles every module on every launch. The script uses
`compileall` with `UNCHECKED_HASH` so the `.pyc` files stay valid when
packaging resets mtimes, and it skips the install when
`MESON_INSTALL_DRY_RUN` is set. Keep it in the install path when adding a new
Python module or package directory.

### AppImage

`./scripts/build-appimage.sh` builds `dist/hello-<version>-x86_64.AppImage` in
an `ubuntu:26.04` container. It assembles the AppDir with `appimage-builder`,
then repacks it with a pinned official `appimagetool` and the statically linked
type2 runtime (`squashfuse_ll` plus libfuse3). Podman or Docker and network
access are required.

The tool versions and SHA-256 sums live in `scripts/build-appimage.sh`. Bump
them together and rerun the release AppImage smoke test. `appimagetool` 1.9.1
also needs the `file` package, and `appimage-builder` 1.1.0 needs the local apt
version-comparison patch the script applies.

Verify without mounting the payload:

```sh
./dist/hello-*-x86_64.AppImage --appimage-version
./dist/hello-*-x86_64.AppImage --appimage-extract
./squashfs-root/AppRun --help
```

The launcher resolves `APPDIR` before the configured prefix, so bundled
schemas, icons and translations load from the mount. Without FUSE3, use
`--appimage-extract-and-run`. See `docs/appimage.md` for runtime behavior,
profiling and limits.

### Scoped application CSS

`Adw.Application` automatically loads `style.css`, `style-dark.css` and
`style-hc.css` from the application's GResource base path. Add `style.css` to
`src/hello.gresource.xml`; no Python loader is needed:

```xml
<file>style.css</file>
```

Keep selectors scoped to your own classes (for example `.markdown-table`) and
use Adwaita named colors such as `@borders`, `@card_bg_color` and
`@accent_bg_color` so both themes keep working.

If you use a plain `Gtk.Application` or need a runtime-generated provider, load
the file explicitly during `do_startup()`:

```python
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk

provider = Gtk.CssProvider()
provider.load_from_resource('/com/example/Hello/style.css')
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
)
```

## File index

```text
[Refs]|Blueprint syntax, bindings, menus, breakpoints: .agents/skills/gtk-guidelines/SKILL.md
[UI]|sources: src/*.blp | generated, do not edit: build/src/*.ui
     |entry: src/main.py (app + actions), src/window.py (window class)
     |resources: src/hello.gresource.xml, src/style.css | build: src/meson.build
[Data]|settings: data/com.example.Hello.gschema.xml | i18n: po/POTFILES.in
      |desktop/metainfo: data/*.in | flatpak: com.example.Hello.json
[Tools]|dev.py, scripts/init.py, scripts/test.py (sanitized test runner)
       |scripts/compile-bytecode.py (install-time bytecode)
       |scripts/build-appimage.sh, packaging/appimage/AppImageBuilder.yml
       |tests/test_init.py, tests/test_window.py, tests/test_lifecycle.py,
       |tests/test_startup.py
[Docs]|README.md, AGENTS.md, docs/README.md, docs/flathub.md,
      |docs/appimage.md, docs/releasing.md
[CI]|.github/workflows/ci.yml, .github/workflows/release.yml
```

## Gotchas

- Composite-template roots must be subclassable: libadwaita marks some widgets
  final (`Adw.OverlaySplitView`, `Adw.HeaderBar`), so a template rooted at one
  fails at import. Wrap it in `Adw.Bin` and subclass that.
- Blueprint object-valued properties end with `;` after the closing brace:
  `content: Adw.ToolbarView { ... };`. Slots such as `[top]` are not values.
- Blueprint imports are `using Gtk 4.0;` and `using Adw 1;` — never `1.x`.
- Blueprint `bind` expressions cannot cross composite-template boundaries.
  Wire cross-template bindings in Python (`GObject.bind_property`).
- Blueprint extension blocks (`strings [...]`, `marks [...]`, `responses
  [...]`) and `template` blocks never take a trailing `;`.
- `GtkListView` `header-factory` templates must be `template ListHeader`
  (`GtkListHeader`); a `template ListItem` compiles but fails at runtime.
- `Adw.ActionRow` parses title/subtitle as Pango markup by default. Set
  `use-markup` false before setting plain text containing `&` or `<`.
- `Gtk.StringList` has no insert method — use `splice(position, 0, [value])`.
- Add every new `.blp` to the blueprint name list in `src/meson.build`; the
  foreach creates an explicit `.ui` output and the gresource depends on it.
  If a UI change doesn't show up, run `ninja -C build -d explain`.
- GtkSource GTypes register lazily. If a Blueprint template contains
  `GtkSourceView`, instantiate `GtkSource.View()` before `Gtk.Template`
  builds the template; otherwise GtkBuilder fails with
  `Invalid object type 'GtkSourceView'`.
- `Gtk.Picture` with `can_shrink=True` can be allocated zero height inside a
  scrolled or clamped view, especially after loading an SVG. Set an explicit
  height request based on the paintable's intrinsic size (capped to a sensible
  maximum), or use `can_shrink=False` when the image should keep its natural
  size.
- `Gio.File.replace_contents_async()` does not keep a Python `bytes` payload
  alive for the duration of the write. Keep the encoded payload in the
  callback data, for example
  `file.replace_contents_async(data, ..., callback, data)`, or the file can be
  filled with freed-memory garbage.
- `Gtk.FileDialog.open()` invokes its callback with `(source_object, result)`
  only. Pass user data after the callback if the handler needs it, and declare
  the matching parameter.
- Pango markup is not HTML. Escape every dynamic text fragment with
  `GLib.markup_escape_text` before putting it in a `Gtk.Label` that uses markup.
- `blocks, _ = ...` shadows gettext's `_()` in that function and raises
  `UnboundLocalError` on a later `_("...")`. Use `_ignored` or another name.
- `Gtk.Label` has an `activate-link` signal even when
  `GObject.signal_list_names` does not show it; connect it normally and return
  `True` to suppress the default handler.
- If a Flatpak source archive is flattened, Meson fails with
  `first statement must be a call to project()`. Create archive sources with a
  top-level directory (`git archive --prefix="hello-$VERSION/"`).
- Flathub's `flatpak-builder-lint` maps `io.github.<owner>.<App>` to
  `https://github.com/<owner>/<app>`. A repository named `my-app` fails
  `appid-url-not-reachable`; name the repository to match the last app ID
  component without hyphens, or use a domain-based ID.
- `appimagetool` 1.9.1 needs the `file` package in the build container.
  `appimage-builder` 1.1.0 needs the apt version-comparison patch applied by
  `scripts/build-appimage.sh`; keep both when bumping the tool.
- Before planning UI around a widget not yet used here, verify availability
  (`python3 -c "import gi; gi.require_version('Adw','1'); from gi.repository
  import Adw; print(Adw.MultiLayoutView)"`), and probe Blueprint syntax by
  compiling a minimal snippet in `/tmp` — don't rely on docs alone.

<!-- template:start -->
## Template initialization

Run `python3 scripts/init.py` from a copy of this repository to replace the
app ID, name, slug, author and derived filenames. It validates code-hosting IDs
against the repository URL before changing anything. It also removes the
template-only sections from `README.md` and this file. The script and its tests
are excluded from replacements, so the template defaults remain available for
the next copy. Once a project is initialized, `scripts/init.py` and
`tests/test_init.py` are no longer needed and can be deleted together.
<!-- template:end -->
