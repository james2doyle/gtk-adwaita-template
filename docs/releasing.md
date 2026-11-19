# Releasing Hello

Releases are built from an annotated tag, not from an arbitrary working tree.
The version comes from `pyproject.toml` (the AppImage script reads it) and
`meson.build`; keep `pyproject.toml` and
`data/com.example.Hello.metainfo.xml.in` in sync.

## Prepare

1. Set the new version in `meson.build`, `pyproject.toml`, and the AppStream
   release entry. Update the AppStream screenshot URL to the new tag.
2. Run the checks:

   ```sh
   meson compile -C build
   python3 scripts/test.py
   uvx pyright src tests scripts dev.py
   uvx ruff check --select E9,F63,F7,F82,F401,I001 \
     src tests scripts dev.py
   for file in src/*.blp; do
     blueprint-compiler compile "$file" >/dev/null
     blueprint-compiler lint "$file"
   done
   sh -n scripts/build-appimage.sh
   ```

3. Commit and push the release, then create and push the tag:

   ```sh
   export VERSION=0.1.0
   export TAG="v$VERSION"

   git tag -a "$TAG" -m "Hello $VERSION"
   git push origin main
   git push origin "$TAG"
   ```

## Flatpak release bundle

The development manifest builds the working tree and does not set a release
build type. For a release, create an archive from the tag and a derived
manifest with a SHA-256-pinned `archive` source and `--buildtype=release`:

```sh
export VERSION=0.1.0
export TAG="v$VERSION"

rm -rf dist build-flatpak .flatpak-builder
mkdir -p dist

git archive --format=tar.gz --prefix="hello-$VERSION/" \
  -o "dist/hello-$VERSION.tar.gz" "$TAG"

sha=$(sha256sum "dist/hello-$VERSION.tar.gz" | cut -d' ' -f1)
python3 - "$sha" "hello-$VERSION.tar.gz" <<'PY'
import json
import sys
from pathlib import Path

sha = sys.argv[1]
archive = sys.argv[2]
manifest = json.loads(Path("com.example.Hello.json").read_text())
module = manifest["modules"][0]
module["sources"] = [{
    "type": "archive",
    "path": archive,
    "sha256": sha,
}]
module["config-opts"] = ["--libdir=lib", "--buildtype=release"]
Path("dist/com.example.Hello.release.json").write_text(
    json.dumps(manifest, indent=4) + "\n"
)
PY
```

The release workflow fills in the same values from the tag.

```sh
flatpak-builder --force-clean --repo=dist/repo --state-dir=.flatpak-builder \
  --default-branch=stable --subject="Hello $VERSION" \
  build-flatpak "dist/com.example.Hello.release.json"

flatpak build-bundle dist/repo "dist/hello-$VERSION.flatpak" \
  com.example.Hello stable
```

The archive must have a top-level directory (`--prefix=...`). Flatpak strips
one leading path component when extracting; without it the source tree is
flattened and Meson fails with `first statement must be a call to project()`.

On a machine without the GNOME 51 runtime and SDK, add
`--user --install-deps-from=flathub` to the `flatpak-builder` command.

## AppImage release build

The AppImage is built from the tagged source in an Ubuntu 26.04 container. The
build script reads the version from `pyproject.toml`; set `VERSION` only when
testing a tag checkout whose version matches. It pins `appimagetool` and the
official type2 runtime, verifies their SHA-256 sums, and repacks the AppDir
with that runtime.

```sh
export VERSION=0.1.0

./scripts/build-appimage.sh
sha256sum "dist/hello-$VERSION-x86_64.AppImage"
```

The artifact is written to `dist/hello-$VERSION-x86_64.AppImage`. See
[appimage.md](appimage.md) for runtime behavior, FUSE fallback and limits.

Smoke-test the artifact without installing it:

```sh
APPIMAGE="dist/hello-$VERSION-x86_64.AppImage"
"$APPIMAGE" --appimage-version
"$APPIMAGE" --appimage-extract
./squashfs-root/AppRun --help
```

## Verify and install

```sh
export VERSION=0.1.0

flatpak install --user --reinstall "dist/hello-$VERSION.flatpak"
flatpak info --user com.example.Hello
flatpak run com.example.Hello
```

`flatpak build-bundle` produces an unsigned local bundle. Flathub builds the
app from a manifest, so use a URL-backed archive (for example the GitHub tag
tarball) and let Flathub sign and build it.

For a local install test without touching your normal Flatpak installation:

```sh
tmp=$(mktemp -d)
FLATPAK_USER_DIR="$tmp" flatpak install --user --noninteractive \
  "dist/hello-$VERSION.flatpak"
FLATPAK_USER_DIR="$tmp" flatpak run com.example.Hello --help
rm -rf "$tmp"
```

The release workflow runs the same install-and-help check on the bundle it
publishes.

## Automated GitHub release

`.github/workflows/release.yml` runs after the **CI** workflow succeeds for a
`v*.*.*` tag push. It is deliberately separate from `ci.yml` so CI stays
read-only and releases cannot be published from pull requests or `main` pushes.
CI runs on pull requests, `main` pushes, and `v*.*.*` tag pushes.

The workflow:

- skips anything that is not a `v*.*.*` tag push, including branches and pull
  requests, before the build job starts;
- checks out the tagged commit and creates the same prefixed source archive and
  pinned release manifest shown above;
- builds the Flatpak with `--buildtype=release`;
- installs the built bundle into a temporary `FLATPAK_USER_DIR` and smoke-runs
  `flatpak run com.example.Hello --help`;
- builds the AppImage in an Ubuntu 26.04 container with the pinned
  `appimagetool` and type2 runtime, extracts it, checks
  `--appimage-version`, and smoke-runs `AppRun --help` plus an Xvfb launch;
- uploads the source archive, release manifest, Flatpak, AppImage, and
  `SHA256SUMS` to a GitHub Release;
- updates assets with `--clobber` if the release already exists, making
  re-runs safe.

The release is published, not drafted. Add `--draft` to the `gh release create`
command in the workflow if you prefer a manual approval step.

## Artifacts

`dist/` is gitignored. A successful release build produces:

- `dist/hello-$VERSION.tar.gz` — tagged source archive
- `dist/com.example.Hello.release.json` — pinned release manifest
- `dist/hello-$VERSION.flatpak` — installable bundle
- `dist/hello-$VERSION-x86_64.AppImage` — portable AppImage
- `dist/repo/` — local OSTree repository
