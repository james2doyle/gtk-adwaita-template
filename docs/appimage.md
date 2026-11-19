# AppImage

The AppImage is an x86_64 single-file build for Linux desktops that cannot or
do not want to use Flatpak. It bundles the app, Python, PyGObject, GTK 4,
libadwaita, GSettings schemas, icons and translations.

The build is intentionally not run on the host. `appimage-builder` resolves
runtime packages from Ubuntu 26.04 and uses its AppRun runtime to select a
compatible glibc at launch. The final artifact is repacked with the official
statically linked type2 runtime (`squashfuse_ll` plus libfuse3), so libfuse2 is
not required. Podman or Docker is required.

## Build

```sh
./scripts/build-appimage.sh
```

The script:

1. reads the version from `pyproject.toml` unless `VERSION` is set;
2. starts an `ubuntu:26.04` container;
3. installs Meson, Blueprint, GTK and libadwaita build tools;
4. installs `appimage-builder` 1.1.0 with a Python 3.12 tool environment;
5. builds the app with `--buildtype=release` and installs it into the AppDir;
6. bundles runtime packages from the Ubuntu 26.04 archive;
7. verifies and unpacks the pinned official `appimagetool` and type2 runtime;
8. repacks the AppDir with the type2 runtime and writes
   `dist/hello-<version>-x86_64.AppImage`.

The tool versions and their SHA-256 sums live in
`scripts/build-appimage.sh`. Update both together when bumping the runtime, and
rerun the release AppImage smoke test.

The first build downloads the container image and package metadata, so it
needs network access and takes several minutes. Later builds reuse the podman
image and are faster.

Use a release version explicitly when testing a tag build:

```sh
VERSION=0.1.0 ./scripts/build-appimage.sh
```

## Run and verify

```sh
chmod +x dist/hello-0.1.0-x86_64.AppImage
./dist/hello-0.1.0-x86_64.AppImage
```

Confirm the embedded runtime without mounting the payload:

```sh
./dist/hello-0.1.0-x86_64.AppImage --appimage-version
# AppImage runtime version: https://github.com/AppImage/type2-runtime/commit/...
```

Without FUSE, use the runtime's extract-and-run option:

```sh
./dist/hello-0.1.0-x86_64.AppImage --appimage-extract-and-run
```

Extract and check the launcher without a display:

```sh
./dist/hello-0.1.0-x86_64.AppImage --appimage-extract
./squashfs-root/AppRun --help
```

The release workflow starts the extracted AppRun under Xvfb and treats a
timeout as success, because the app stays open until the user closes it.

## Profiling

The bundle carries its own Python and GTK runtime, so profile the extracted
AppDir. `AppRun` sets `PYTHONHOME`, `PYTHONPATH` and the library path the
bundled interpreter needs; invoking `squashfs-root/usr/bin/python3` directly
does not work. Profiling the mounted AppImage also includes FUSE file I/O,
which is not application time.

```sh
./dist/hello-0.1.0-x86_64.AppImage --appimage-extract
PYTHONPROFILEIMPORTTIME=1 ./squashfs-root/AppRun --help 2>importtime.txt
sort -t'|' -k2 -nr importtime.txt | head -20
```

Release installs ship `unchecked-hash` bytecode, so this measures real start
cost rather than first-run compilation. For CPU samples, use py-spy:

```sh
uvx py-spy record -o hello.svg --rate 100 --duration 10 \
  -- ./squashfs-root/AppRun
```

For GTK, layout and main-loop time, use Sysprof with the GTK trace points:

```sh
sysprof-cli --gtk --use-trace-fd hello.syscap -- ./squashfs-root/AppRun
```

## Runtime behavior

- The payload is mounted by the statically linked official type2 runtime. It
  uses `squashfuse_ll` and libfuse3, so the host does not need libfuse2.
- Settings and app state use the normal XDG directories. The AppImage does not
  write into its own mount.
- `APPDIR` makes the installed launcher resolve `share/hello`, translations,
  schemas and icons inside the bundle. A normal system install keeps using the
  configured prefix.
- Fonts, input methods, the GL/EGL loader and GPU drivers come from the host.

## Limits

- The artifact is unsigned and has no update metadata. Download it from the
  release page and verify the published `SHA256SUMS`.
- It targets x86_64 only.
- A working FUSE3 setup (`/dev/fuse` and `fusermount3`) is still required for
  the default mount mode. Hosts without it can use
  `--appimage-extract-and-run`.
- Flatpak remains the recommended distribution format for a fully sandboxed
  install and desktop integration.

## Troubleshooting

If the AppImage does not start, run it with `--appimage-extract-and-run` to
bypass FUSE. If GTK reports a missing display or graphics library, confirm the
host has working X11 or Wayland and GPU drivers. See the Debugging section in
`AGENTS.md` for local build and stale-UI checks.
