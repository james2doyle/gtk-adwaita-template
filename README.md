# Hello

A minimal GTK 4 + libadwaita application scaffold for Python.

Hello is a working starting point for a GNOME application: a Blueprint UI,
`Adw.Application` lifecycle, gettext translations, GSettings, desktop and
AppStream metadata, a Flatpak manifest, a restart-on-save development runner,
and a Meson test setup.

## What you get

- GTK 4 and libadwaita with PyGObject
- Blueprint (`.blp`) UI sources compiled to GtkBuilder XML at build time
- Meson build with a local-prefix install for uninstalled runs
- gettext translation wiring and AppStream/desktop-file validators
- GSettings schema and D-Bus activation service
- Flatpak manifest targeting `org.gnome.Platform` 50
- `dev.py` restart-on-save runner and a window smoke test

## Requirements

- Python 3.12+ and PyGObject (`Gtk-4.0`, `Adw-1` GIRs)
- GTK 4 and libadwaita
- `meson`, `ninja`, `blueprint-compiler`
- `gettext` (`msgfmt`); optional validators: `desktop-file-validate`,
  `appstreamcli`, `glib-compile-schemas`
- `flatpak` and `flatpak-builder` for packaging

## Create a project from this template

Copy the directory (or use it as a GitHub template), then run the initializer
from the new copy:

```sh
python3 scripts/init.py \
  --app-id com.example.MyApp \
  --name "My App" \
  --author "Your Name" \
  --author-email you@example.com
```

Run `python3 scripts/init.py` without arguments to be prompted for each value.
The script rewrites the application ID, resource path, GType prefix, human
name, slug, author, URLs, and every derived filename (desktop file, schema,
service, Flatpak manifest, icons, launcher, gresource).

Rules:

- The app ID must be a reverse-DNS D-Bus name with at least three components,
  such as `com.example.MyApp`.
- The slug must be a lowercase Python identifier. It is derived from the name
  when `--slug` is omitted (`"My App"` becomes `my_app`).
- The initializer skips itself, so it keeps the template defaults for a
  future copy.

## Build and run

```sh
meson setup build --prefix="$PWD/build-install"   # once
meson compile -C build
meson install -C build
./build-install/bin/hello
```

The launcher hard-codes the install prefix, so uninstalled runs need the
`build-install` prefix and the `meson install` step.

## Live development

`dev.py` watches `src/`, `data/` and the top-level `meson.build`. On a change
to a `.blp`, Python, CSS, XML or data file it rebuilds, reinstalls and
relaunches the app. It starts with the GTK Inspector enabled
(`GTK_DEBUG=interactive`) unless `GTK_DEBUG` is already set.

```sh
python3 dev.py
GTK_DEBUG= python3 dev.py   # without the inspector
```

Ctrl+C or SIGTERM stops the watcher and the app.

## Tests

```sh
meson test -C build
```

Runs the desktop/appstream/schema validators and the window smoke test. The
test environment uses scratch XDG directories and no session bus, so it does
not touch user data.

## Flatpak

The manifest builds the app from the working tree (`type: dir`), so
uncommitted changes are included. A stale local `build/` directory can break
the module build; remove it first.

```sh
rm -rf build
flatpak-builder --user --install --force-clean build-flatpak com.example.Hello.json
flatpak run com.example.Hello
```

The manifest targets the GNOME runtime `50`. Add `--talk-name` or other
finish-args only when the application actually needs them.

## Project layout

```text
dev.py                         restart-on-save development runner
com.example.Hello.json         Flatpak manifest
pyproject.toml                 Python metadata and uv dependency groups
data/                          desktop file, metainfo, GSettings schema, icons
po/                            translation sources
scripts/init.py                rename the scaffold for a new application
src/hello.in                   entry script template (paths set by Meson)
src/main.py                    Adw.Application: actions and lifecycle
src/window.py                  main window class (composite template)
src/window.blp                 main window UI
src/shortcuts-dialog.blp       keyboard shortcuts dialog
src/hello.gresource.xml        resource bundle definition
src/meson.build                UI/resource/launcher/source build rules
tests/test_window.py           window smoke test
.agents/skills/                GTK and libadwaita reference skills
```

## Customizing

1. Replace the placeholder summary, description, screenshots, developer,
   homepage, and branding colors in `data/com.example.Hello.metainfo.xml.in`.
2. Bump the version in three places: `meson.build`, the About dialog in
   `src/main.py`, and `pyproject.toml`.
3. Add GSettings keys to `data/com.example.Hello.gschema.xml` before using
   them from Python.
4. Add translatable files to `po/POTFILES.in`; wrap user-visible strings in
   `_(...)` in Python and `.blp` files.
5. Follow `AGENTS.md` for window/dialog and action workflows.

## License

MIT — see [COPYING](COPYING). AppStream metadata is CC0-1.0.
