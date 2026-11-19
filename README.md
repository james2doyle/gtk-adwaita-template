# Hello

A minimal GTK 4 + libadwaita application scaffold for Python.

Hello is a working starting point for a GNOME application: a Blueprint UI,
`Adw.Application` lifecycle, gettext translations, GSettings, desktop and
AppStream metadata, a Flatpak manifest, a containerized AppImage build, a
restart-on-save development runner, and a Meson test setup.

## What you get

- GTK 4 and libadwaita with PyGObject
- Blueprint (`.blp`) UI sources compiled to GtkBuilder XML at build time
- Meson build with a local-prefix install for uninstalled runs
- gettext translation wiring and AppStream/desktop-file validators
- GSettings schema and D-Bus activation service
- Flatpak manifest targeting `org.gnome.Platform` 51
- AppImage build with the official type2 runtime and pinned `appimagetool`
- Install-time bytecode compilation for read-only installs
- GitHub Actions build/lint/test workflow with pinned actions, an installed
  launcher smoke test, and a conditional Flatpak lint job
- Tag-gated release workflow for source, Flatpak and AppImage artifacts
- `dev.py` restart-on-save runner, a sanitized test runner, initializer tests,
  a window smoke test, an application lifecycle test, and a lazy-import guard

## Requirements

- Python 3.12+ and PyGObject (`Gtk-4.0`, `Adw-1` GIRs)
- GTK 4 and libadwaita 1.8+ (the Flatpak runtime provides 1.10)
- `meson`, `ninja`, `blueprint-compiler`
- `gettext` (`msgfmt`); optional validators: `desktop-file-validate`,
  `appstreamcli`, `glib-compile-schemas`
- `flatpak` and `flatpak-builder` for packaging
- podman or Docker and network access for AppImage builds
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
python3 scripts/test.py
meson install -C build
./build-install/bin/my_app
```

After initialization, `scripts/init.py` and `tests/test_init.py` are no
longer needed. Delete both if you don't want to keep the template defaults in
the new project.

Rules:

- The app ID must be a reverse-DNS D-Bus name with at least three components,
  such as `com.example.MyApp`.
- The slug must be a lowercase Python identifier. It is derived from the name
  when `--slug` is omitted (`"My App"` becomes `my_app`).
- The initializer skips itself and its tests, so they keep the template
  defaults for a future copy.
<!-- template:end -->

## Build and run

```sh
meson setup build --prefix="$PWD/build-install"   # once
meson compile -C build
python3 scripts/test.py
meson install -C build
./build-install/bin/hello
```

The launcher hard-codes the install prefix, so uninstalled runs need the
`build-install` prefix and the `meson install` step. It also adds that prefix
to `GSETTINGS_SCHEMA_DIR` and `XDG_DATA_DIRS`, so schemas and icons resolve
without extra environment setup. AppImage runs use `APPDIR` instead, so the
same launcher resolves the bundled prefix when it is present.

## Startup performance

The window is presented before deferred work. `src/main.py` lazy-imports the
window, and installs ship `unchecked-hash` bytecode so read-only Flatpak and
AppImage trees do not recompile on every launch. See the Startup performance
section in `AGENTS.md` for the profiling commands and the deferred-work rules.

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
python3 scripts/test.py
```

`scripts/test.py` removes stale Meson test logs and runs the suite with an
allow-listed environment, so API keys and tokens from your shell are not
copied into `build/meson-logs`. It runs the desktop/appstream/schema
validators, initializer tests, a window smoke test, an application lifecycle
test, and a fresh-subprocess lazy-import guard. GUI tests skip themselves when
no display is available. The test environment uses scratch XDG directories and
no session bus, so it does not touch user data. Tests that assert deferred
startup work must drain `GLib.MainContext` before checking state.

## Debugging

Prefer adding a test under `tests/` over driving the running UI with
automation tools. Headless tests cover logic; in-process widget tests inspect
the real GTK widget tree and are reproducible. Use
`python3 scripts/test.py` while iterating, `GTK_DEBUG=interactive`
to open the GTK Inspector, and `G_DEBUG=fatal-criticals` to stop on GTK
criticals. Use `HELLO_DEBUG=1` for the app's Python debug logging;
`G_MESSAGES_DEBUG` controls GLib's own log domains. Never drive the GUI or send
input without explicit permission; see the Debugging section in `AGENTS.md`.

## Flatpak

The manifest builds the app from the working tree (`type: dir`), so
uncommitted changes are included. That is suitable for local development, not
a reproducible release. `COPYING` is explicitly installed and declared in the
manifest.

```sh
flatpak-builder --user --install --force-clean build-flatpak com.example.Hello.json
flatpak run com.example.Hello
```

The manifest targets the GNOME runtime `51`. Add `--talk-name` or other
finish-args only when the application actually needs them.

## AppImage

```sh
./scripts/build-appimage.sh
./dist/hello-*-x86_64.AppImage
```

The build runs in an `ubuntu:26.04` container, assembles the AppDir with
`appimage-builder`, then repacks it with a pinned official `appimagetool` and
the statically linked type2 runtime (`squashfuse_ll` plus libfuse3). Podman or
Docker and network access are required. libfuse2 is not.

Verify the runtime and payload without mounting:

```sh
./dist/hello-*-x86_64.AppImage --appimage-version
./dist/hello-*-x86_64.AppImage --appimage-extract
./squashfs-root/AppRun --help
```

Without FUSE3, use `--appimage-extract-and-run`. See
[docs/appimage.md](docs/appimage.md) for the build steps, runtime behavior,
profiling and limits.

## Release checklist

Before publishing or submitting to Flathub:

1. Initialize the identity, bump the version in `meson.build`, `pyproject.toml`
   and the AppStream release entry, and replace placeholder metadata.
2. Add at least one public AppStream screenshot. Use a direct HTTP(S) image
   URL pinned to a tag or commit, mark one screenshot as `type="default"`, and
   give it a short caption. Do not use a branch URL or GitHub `/blob/` page.
3. Replace the development manifest's `"type": "dir"` source with a public Git
   commit or source archive with a digest. Do not release from an unpinned
   working tree. For an archive, create it with a top-level directory
   (`git archive --prefix="hello-$VERSION/"`) and use
   `--buildtype=release` in the manifest. The release workflow does both
   automatically.
4. Build the repository and run `flatpak-builder-lint manifest
   com.example.Hello.json` followed by `flatpak-builder-lint repo <repo>`.
5. Verify the installed app contains `COPYING` under
   `share/licenses/<app-id>/` and launches from the installed launcher.
6. Build and smoke-test the release artifacts. For the Flatpak, install the
   bundle into a temporary `FLATPAK_USER_DIR` and run
   `flatpak run com.example.Hello --help`. For the AppImage, check
   `--appimage-version`, extract it, and run `squashfs-root/AppRun --help`.
   See [docs/releasing.md](docs/releasing.md) for the full flow.
7. Confirm no `.env`, keys, tokens, credentials, or test logs are tracked, and
   rotate any credential that may have been logged before the sanitized test
   runner was added.

## Optional additions

- **GtkSourceView**: the template does not use it, but GNOME applications
  often do. Install `gtksourceview5` (and add it to the CI `dnf install` list)
  before adding a `GtkSource.View`. PyGObject registers its GTypes lazily, so
  call `GtkSource.View()` in the window's `__init__` before
  `super().__init__()` when a Blueprint contains `GtkSourceView`. The GNOME
  Flatpak runtime already includes GtkSourceView 5; add a module if you target
  another runtime.
- **Vendored Python packages**: install pure-Python dependencies with
  `install_subdir()` and exclude both `**/__pycache__` directories and
  `**/*.pyc` files. Add the vendor directory to `sys.path` before importing
  the package.
- **Scoped CSS**: add `style.css` to `src/hello.gresource.xml`; `Adw.Application`
  loads `style.css`, `style-dark.css` and `style-hc.css` from the resource base
  path automatically. Prefix selectors with your own classes and use Adwaita
  named colors so light and dark themes keep working. Load CSS manually only
  for a plain `Gtk.Application` or a runtime-generated provider.
- **Startup profiling**: use `PYTHONPROFILEIMPORTTIME=1`, `GDK_DEBUG=frames`,
  py-spy and Sysprof before optimizing. Keep expensive highlighting, preview
  and spell-check work after `present()`; see `AGENTS.md`.
- **AppImage**: `./scripts/build-appimage.sh` builds a modern type2-runtime
  artifact in a container. See [docs/appimage.md](docs/appimage.md) for runtime
  behavior and FUSE fallback.
- **Async file/network work**: follow the ownership, generation, cancellation,
  snapshot, and resource-limit guidance in `AGENTS.md` before adding I/O.

## Project layout

```text
.github/workflows/ci.yml  GitHub Actions build/lint/test workflow
.github/workflows/release.yml  tag-gated release workflow
COPYING                   MIT license
dev.py                    restart-on-save development runner
com.example.Hello.json    Flatpak development manifest
pyproject.toml            dev tooling metadata (not a Python package)
data/                     desktop file, metainfo, GSettings schema, icons
docs/appimage.md          AppImage build and runtime notes
docs/releasing.md         release builds, Flatpak and AppImage
packaging/appimage/AppImageBuilder.yml  appimage-builder recipe
po/                       translation sources
scripts/init.py           rename the scaffold for a new application
scripts/test.py           sanitized Meson test runner
scripts/build-appimage.sh modern AppImage build wrapper
scripts/compile-bytecode.py  install-time bytecode compiler
src/hello.in              entry script template (paths set by Meson)
src/main.py               Adw.Application: actions and lifecycle
src/window.py             main window class (composite template)
src/window.blp            main window UI
src/shortcuts-dialog.blp  keyboard shortcuts dialog
src/style.css             app CSS loaded automatically by Adw.Application
src/hello.gresource.xml   resource bundle definition
src/meson.build           UI/resource/launcher/source build rules
tests/test_init.py        headless initializer tests
tests/test_window.py      window smoke test (skips without a display)
tests/test_lifecycle.py   application Quit and teardown tests
tests/test_startup.py     lazy-import guard
.agents/skills/           GTK and libadwaita reference skills
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
`python3 scripts/test.py`, lint changed `.blp` files with
`blueprint-compiler lint`, and keep `uvx pyright src tests scripts dev.py` and
`uvx ruff check --select E9,F63,F7,F82,F401,I001 src tests scripts dev.py`
clean when `uv` is available. If you touch the AppImage script or recipe, run
`sh -n scripts/build-appimage.sh`. Prefer adding a test under `tests/` over
driving the UI with automation tools; see the Debugging section in `AGENTS.md`.

## License

MIT — see [COPYING](COPYING). AppStream metadata is CC0-1.0.
