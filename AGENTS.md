# AGENTS.md — Hello

GTK 4 + libadwaita application in Python 3 (PyGObject), with Blueprint UI
(`.blp` compiles to GtkBuilder XML at build time), Meson, gettext i18n and
Flatpak packaging. App ID: `com.example.Hello`.

IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning for
GTK4/libadwaita/Blueprint tasks.

## Finding documentation

- GTK: https://docs.gtk.org/gtk4/
- GTK search: https://docs.gtk.org/gtk4/?q=%s
- libadwaita: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.9/index.html?q=%s
- libadwaita stylesheet: https://github.com/GNOME/libadwaita/tree/1.9.4/src/stylesheet

## Build & verify

```sh
meson setup build --prefix="$PWD/build-install"  # once
meson compile -C build
meson test -C build
meson install -C build
./build-install/bin/hello
blueprint-compiler compile src/window.blp
blueprint-compiler lint src/window.blp
```

Definition of done for a change: `blueprint-compiler compile` on touched
`.blp` files, `meson test -C build` green, full `meson compile -C build`, and
the app launches via `./build-install/bin/hello`. Lint each touched `.blp`
file as the final step.

`dev.py` rebuilds and relaunches on save:

```sh
python3 dev.py
```

## Hard boundaries

- Don't edit `src/*.ui` — generated from `.blp` by `blueprint-compiler
  batch-compile` (see `src/meson.build`).
- Don't leave user-visible strings unwrapped. Wrap them in `_(...)` in
  `.py`/`.blp` and add the file to `po/POTFILES.in`.
- Don't import gi repositories unguarded. Call `gi.require_version` first
  (`Gtk` `4.0`, `Adw` `1`, and any other repository).
- Don't hand-style widgets with custom CSS. Use Adwaita style classes in
  `styles [...]` blocks in `.blp`.
- Don't read/write settings ad hoc. Add the key to
  `data/com.example.Hello.gschema.xml` first, then use `Gio.Settings`.
- Don't persist app data ad hoc. Add a dedicated storage module with explicit
  schema/versioning if the app needs persistence.
- Keep Meson source/file lists explicit — no globbing.

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

## Workflow: new window or dialog

1. Create `src/foo.blp`. Base it on the skeleton in
   `.agents/skills/gtk-guidelines/SKILL.md`.
2. Add `foo.blp` to the `blueprints` `files(...)` list in `src/meson.build`.
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

## File index

```text
[Refs]|Blueprint syntax, bindings, menus, breakpoints: .agents/skills/gtk-guidelines/SKILL.md
[UI]|sources: src/*.blp | generated, do not edit: src/*.ui
     |entry: src/main.py (app + actions), src/window.py (window class)
     |resources: src/hello.gresource.xml | build: src/meson.build
[Data]|settings: data/com.example.Hello.gschema.xml | i18n: po/POTFILES.in
      |desktop/metainfo: data/*.in | flatpak: com.example.Hello.json
[Tools]|dev.py, tests/test_window.py, scripts/init.py
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
- If a UI change doesn't show up, `touch` the `.blp` or delete the stale
  `build/src/*.ui`; `ninja -C build -d explain` shows why.
- Before planning UI around a widget not yet used here, verify availability
  (`python3 -c "import gi; gi.require_version('Adw','1'); from gi.repository
  import Adw; print(Adw.MultiLayoutView)"`), and probe Blueprint syntax by
  compiling a minimal snippet in `/tmp` — don't rely on docs alone.

## Template initialization

Run `python3 scripts/init.py` from a copy of this repository to replace the
app ID, name, slug, author and derived filenames. The script is excluded from
its own replacements, so the template defaults remain available for the next
copy.
