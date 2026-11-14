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
- Flatpak manifest targeting `org.gnome.Platform` 51
- GitHub Actions build/test workflow
- `dev.py` restart-on-save runner and a window smoke test

## Requirements

- Python 3.12+ and PyGObject (`Gtk-4.0`, `Adw-1` GIRs)
- GTK 4 and libadwaita 1.5+ (the Flatpak runtime provides 1.10)
- `meson`, `ninja`, `blueprint-compiler`
- `gettext` (`msgfmt`); optional validators: `desktop-file-validate`,
  `appstreamcli`, `glib-compile-schemas`
- `flatpak` and `flatpak-builder` for packaging
- optional: `uv` to install the `pygobject-stubs` dev group for editors;
  the application itself always runs on the system Python

<!-- template:start -->
## Start a new project

This repository is a template. Use GitHub's **Use this template** button, or
clone it and start a fresh history:

```sh
git clone https://github.com/james2doyle/gtk-adwaita-template.git my-app
cd my-app
rm -rf .git
git init -b main
```

Skip the history-reset steps if you used **Use this template**.

Then rewrite the template identity from the new project directory:

```sh
python3 scripts/init.py \
  --app-id com.example.MyApp \
  --name "My App" \
  --author "Your Name" \
  --author-email you@example.com \
  --repo-url https://github.com/you/my-app
```

Run `python3 scripts/init.py` without arguments to be prompted for the
application ID, name, author, email and repository URL.
The script rewrites the application ID, resource path, GType prefix, human
name, slug, author, URLs, and every derived filename (desktop file, schema,
service, Flatpak manifest, icons, launcher, gresource).

Review the result, commit the initial project, and build and test it. The
executable name is the derived slug (`"My App"` becomes `my_app`):

```sh
git add -A
git commit -m "Initialize My App"
meson setup build --prefix="$PWD/build-install"
meson compile -C build
meson test -C build
meson install -C build
./build-install/bin/my_app
```

Rules:

- The app ID must be a reverse-DNS D-Bus name with at least three components,
  such as `com.example.MyApp`.
- The slug must be a lowercase Python identifier. It is derived from the name
  when `--slug` is omitted (`"My App"` becomes `my_app`).
- The initializer skips itself, so it keeps the template defaults for a
  future copy.
<!-- template:end -->

## Build and run

```sh
meson setup build --prefix="$PWD/build-install"   # once
meson compile -C build
meson install -C build
./build-install/bin/hello
```

The launcher hard-codes the install prefix, so uninstalled runs need the
`build-install` prefix and the `meson install` step. It also adds that prefix
to `GSETTINGS_SCHEMA_DIR` and `XDG_DATA_DIRS`, so schemas and icons resolve
without extra environment setup.

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
uncommitted changes are included. Its `skip` list excludes build directories,
virtualenvs and VCS metadata.

```sh
flatpak-builder --user --install --force-clean build-flatpak com.example.Hello.json
flatpak run com.example.Hello
```

The manifest targets the GNOME runtime `51`. Add `--talk-name` or other
finish-args only when the application actually needs them.

## Project layout

```text
.github/workflows/ci.yml       GitHub Actions build/test workflow
COPYING                        MIT license
dev.py                         restart-on-save development runner
com.example.Hello.json         Flatpak manifest
pyproject.toml                 dev tooling metadata (not a Python package)
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

1. Replace the placeholder summary, description, developer, homepage, and
   branding colors in `data/com.example.Hello.metainfo.xml.in`, and add at
   least one screenshot before submitting to Flathub.
2. Bump the version in three metadata files: `meson.build`,
   `pyproject.toml` and the `<release>` entry in
   `data/com.example.Hello.metainfo.xml.in`. The About dialog reads the
   version that Meson passes to the launcher.
3. Add GSettings keys to `data/com.example.Hello.gschema.xml` before using
   them from Python.
4. Add translatable files to `po/POTFILES.in`; wrap user-visible strings in
   `_(...)` in Python and `.blp` files.
5. Follow `AGENTS.md` for window/dialog and action workflows.

## Contributing

Pull requests are welcome. Keep the scaffold buildable, run
`meson test -C build`, and lint changed `.blp` files with
`blueprint-compiler lint`.

## License

MIT — see [COPYING](COPYING). AppStream metadata is CC0-1.0.
