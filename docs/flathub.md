# Flathub checklist

This repository's manifest is a development manifest. Flathub builds from a
separate manifest in the Flathub organization's repository, not from this
repository. The GitHub release workflow and Flathub are independent channels.

## App ID and repository

The app ID must be a reverse-DNS D-Bus name with at least three components.
`com.example.Hello` is a placeholder; replace it with a domain you control or a
code-hosting ID before submitting.

Code-hosting IDs have an extra rule:

- `io.github.<owner>.<repo>`, `io.gitlab.<owner>.<repo>`, and
  `page.codeberg.<owner>.<repo>` must have exactly four components.
- The repository must be public and its name must match the last app ID
  component, case-insensitively.
- The repository name must not contain a hyphen when the app ID component does
  not. For example, `io.github.you.MyApp` requires the repository
  `https://github.com/you/MyApp`, not `.../my-app`.
- `scripts/init.py` fails on a mismatch. `flatpak-builder-lint` reports
  `appid-url-not-reachable` or `appid-code-hosting-too-few-components` when the
  rule is broken.

If the repository name cannot match, use a domain-based ID (for example
`com.example.Hello`) instead.

## Required metadata

- App ID matches the desktop file, GSettings schema, D-Bus service, GResource
  prefix, icon names, and the Flatpak manifest.
- `data/com.example.Hello.metainfo.xml.in` has a release entry for the submitted
  version and a public screenshot URL pinned to a tag or commit.
- At least one screenshot is marked `type="default"` and has a short caption.
  Use a direct image URL, not a branch or a GitHub `/blob/` page.
- The desktop file is installed in `share/applications` and declares
  `Icon=com.example.Hello`.
- The metainfo launchable is `com.example.Hello.desktop`.
- A 128×128 scalable icon is installed under
  `data/icons/hicolor/scalable/apps/` and a symbolic icon under
  `data/icons/hicolor/symbolic/apps/`.
- `COPYING` is installed under `share/licenses/<app-id>/` and declared with
  `license-files` in the manifest.
- The version in `meson.build`, `pyproject.toml`, and the AppStream release
  entry are identical.

## Manifest rules

The development manifest uses a `dir` source. Flathub requires a pinned source:

```json
"sources": [
  {
    "type": "archive",
    "url": "https://github.com/you/MyApp/archive/refs/tags/v0.1.0.tar.gz",
    "sha256": "..."
  }
]
```

Do not use a branch, a moving tag, or `type: "dir"`. Use
`--buildtype=release` in `config-opts`:

```json
"buildsystem": "meson",
"config-opts": ["--libdir=lib", "--buildtype=release"]
```

The release workflow builds a local archive-and-digest manifest for the GitHub
release. For Flathub, replace the local `path` source with the public `url`
form above; see [releasing.md](releasing.md#flatpak-release-bundle).

Keep `runtime-version` aligned with the GNOME runtime and SDK the app targets.

## Permissions

The template starts with the minimum permissions:

| Permission | Why |
| --- | --- |
| `--share=ipc` | X11 shared-memory transport |
| `--socket=fallback-x11` | X11 fallback |
| `--socket=wayland` | Wayland |
| `--device=dri` | GTK rendering |

Add permissions only when a feature needs them, and justify each one in the
Flathub pull request. For example, `--share=network` applies to the whole
sandbox because Flatpak has no per-feature network permission.

## Validate before submitting

From the repository root:

```sh
meson compile -C build
python3 scripts/test.py
flatpak-builder-lint manifest com.example.Hello.json
```

Build a repository, then lint it:

```sh
flatpak-builder --force-clean --repo=repo --state-dir=.flatpak-builder \
  build-flatpak com.example.Hello.json
flatpak-builder-lint repo repo
```

Also verify:

- the window and About dialog show the app icon;
- the desktop entry launches the app;
- the screenshot URL resolves at the tagged commit;
- the installed app contains `COPYING` under `share/licenses/<app-id>/`;
- the Flatpak bundle installs into a temporary `FLATPAK_USER_DIR` and runs
  `flatpak run com.example.Hello --help`;
- the AppImage still passes `--appimage-version` and `AppRun --help`.

## Release notes

The AppStream `<release>` entry is the application's canonical release note.
Update it with the new version and date. The GitHub release workflow uses
`--generate-notes`, so its body lists commits; edit the GitHub release if you
want the AppStream summary there too.

## Submission

Follow Flathub's current new-app process and open a pull request against the
Flathub repository with the pinned manifest and a screenshot first. Flathub
rebuilds and signs the application. The `.flatpak` produced by the GitHub release
workflow is for local testing and direct downloads, not the Flathub submission
itself.

If Flathub review requests changes, keep this repository's development manifest
and release notes in sync, but do not weaken the pinned source or runtime
version just to make a local build pass.

## Optional: signed self-hosted repository

Flathub is not the only way to distribute Flatpak updates. The GitHub release
workflow produces a `.flatpak` bundle, but a bundle does not update itself. To
install once and receive later releases with `flatpak update`, publish a signed
repository with [AetherPak](https://github.com/aetherpak/actions).

The setup is one-time:

1. Enable Pages with **Settings → Pages → Build and deployment → Source:
   GitHub Actions**.
2. Create a release GPG key and add the armored private key as the
   `GPG_PRIVATE_KEY` repository secret. Add `GPG_PRIVATE_KEY_PASSPHRASE` when
   the key is protected. AetherPak's
   [signing documentation](https://github.com/aetherpak/actions#signing-optional)
   covers key generation and rotation.
3. If the `github-pages` environment has custom deployment branch policies, add
   a `v*` tag policy. Otherwise a tag deployment is rejected.
4. After the first successful publish, make the application's container package
   public in its package settings. Installs fail while the package is private.

Copy this workflow to `.github/workflows/publish.yml` and adjust the remote name
if desired:

```yaml
name: Publish Flatpak

on:
  push:
    tags: ["v*.*.*"]
  workflow_dispatch:

permissions:
  contents: read
  packages: write
  pages: write
  id-token: write

concurrency:
  group: publish-flatpak
  cancel-in-progress: false

jobs:
  publish:
    uses: aetherpak/actions/.github/workflows/publish.yml@d3803c8feb52143ebb13c8909d2d2a7364eeddef # v3.14.0
    with:
      manifest-path: com.example.Hello.json
      branch: stable
      remote-name: hello
      signing: gpg
    secrets:
      gpg-private-key: ${{ secrets.GPG_PRIVATE_KEY }}
      gpg-private-key-passphrase: ${{ secrets.GPG_PRIVATE_KEY_PASSPHRASE }}
```

The workflow builds `x86_64` and `aarch64`, pushes the images to GHCR, and
deploys the index and landing page to GitHub Pages. The first publish creates
the `.flatpakrepo` and per-app `.flatpakref` files.

Users add the remote and install once:

```sh
flatpak remote-add --user \
  --signature-lookaside=https://OWNER.github.io/REPO/sigs \
  hello https://OWNER.github.io/REPO/hello.flatpakrepo
flatpak install --user hello com.example.Hello
```

Later releases are picked up by:

```sh
flatpak update --user com.example.Hello
```

Replace `OWNER` and `REPO` with the GitHub owner and repository. The
`flatpakrepo` filename follows `remote-name`; if you change `remote-name`,
update both commands. Verified installs need Flatpak 1.17 or newer. On older
clients, use the unsigned remote:

```sh
flatpak remote-add --if-not-exists --user --no-gpg-verify \
  hello oci+https://OWNER.github.io/REPO
flatpak install --user hello com.example.Hello
```
