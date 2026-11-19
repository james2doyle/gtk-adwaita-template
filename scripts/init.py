#!/usr/bin/env python3
"""Initialize this scaffold with a new application identity.

Run this from a copy of the template repository. It rewrites the application
ID, human-readable name, Python/gettext slug, author metadata, resource path,
GType prefix, and every filename derived from the application ID.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APP_ID = "com.example.Hello"
DEFAULT_NAME = "Hello"
DEFAULT_SLUG = "hello"
DEFAULT_AUTHOR = "James Doyle"
DEFAULT_EMAIL = "james2doyle@gmail.com"
DEFAULT_URL = "https://example.com/hello"

CODE_HOSTING_HOSTS = {
    "io.github": "github.com",
    "io.gitlab": "gitlab.com",
    "page.codeberg": "codeberg.org",
}

SKIP_DIRS = {
    ".git",
    ".dex",
    ".delta",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
    ".direnv",
    ".idea",
    ".vscode",
    "build",
    "build-install",
    "build-flatpak",
    "build-appimage",
    "AppDir",
    "appimage-build",
    "squashfs-root",
    ".flatpak-builder",
    ".venv",
    "dist",
    "__pycache__",
}
SKIP_FILES = {
    Path("scripts/init.py"),
    Path("tests/test_init.py"),
}
TEMPLATE_START = "<!-- template:start -->"
TEMPLATE_END = "<!-- template:end -->"
TEMPLATE_FILES = (Path("README.md"), Path("AGENTS.md"))


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def ask(label, default):
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def slugify(name):
    value = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not value:
        fail("the application name must contain at least one letter or digit")
    if value[0].isdigit():
        value = "_" + value
    return value


def validate_app_id(app_id):
    # Reverse-DNS D-Bus name with at least three components, e.g. com.example.App.
    pattern = r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*){2,}"
    if not re.fullmatch(pattern, app_id):
        fail(
            "application ID must be a reverse-DNS D-Bus name with at least "
            "three components (for example com.example.MyApp)"
        )
    parts = app_id.split(".")
    if ".".join(parts[:2]) in CODE_HOSTING_HOSTS and len(parts) != 4:
        fail(
            "code-hosting application IDs must have exactly four components, "
            "for example io.github.you.MyApp"
        )


def validate_repository_identity(app_id, repo_url):
    """Check that a code-hosting app ID names the repository it points at."""
    parts = app_id.split(".")
    host = CODE_HOSTING_HOSTS.get(".".join(parts[:2]))
    if host is None:
        return

    parsed = urlparse(repo_url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if netloc != host:
        fail(
            f"{app_id} requires a {host} repository URL, "
            f"not {repo_url}"
        )

    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    path_parts = [part for part in path.split("/") if part]
    if len(path_parts) != 2:
        fail(
            f"{app_id} requires a repository URL like "
            f"https://{host}/<owner>/<repo>"
        )

    owner, repo = path_parts
    expected_owner, expected_repo = parts[2], parts[3]
    if owner.lower() != expected_owner.lower():
        fail(
            f"{app_id} expects owner {expected_owner!r}, but "
            f"{repo_url} points at {owner!r}"
        )
    if repo.lower() != expected_repo.lower():
        hint = ""
        if "-" in repo:
            hint = (
                " (remove the hyphen from the repository name, or use a "
                "domain-based app ID)"
            )
        fail(
            f"{app_id} expects repository {expected_repo!r}, but "
            f"{repo_url} points at {repo!r}{hint}"
        )


def validate_slug(slug):
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", slug) or not any(
        char.isalnum() for char in slug
    ):
        fail(
            "slug must be a lowercase Python identifier containing at least "
            "one letter or digit"
        )


def validate_text(label, value):
    """Reject characters that need context-specific escaping in source/XML."""
    if not value:
        fail(f"{label} must not be empty")
    for char in value:
        category = unicodedata.category(char)
        if char in "\"'\\<>&" or category in {"Cc", "Cf", "Cs", "Zl", "Zp"}:
            fail(
                f"{label} must not contain quotes, backslashes, angle "
                "brackets, ampersands, or control/format characters"
            )


def validate_email(email):
    validate_text("author email", email)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        fail("author email must look like name@example.com")


def validate_url(url):
    validate_text("repository URL", url)
    if any(char in url for char in "()[]{} \t"):
        fail("repository URL contains characters unsafe for Markdown links")
    try:
        parsed = urlparse(url)
    except ValueError:
        fail("repository URL is not valid")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        fail("repository URL must be an absolute http:// or https:// URL")
    if parsed.username or parsed.password:
        fail("repository URL must not contain embedded credentials")


def gtype_prefix(slug):
    return "".join(part.capitalize() for part in slug.split("_") if part)


def strip_template_sections():
    """Remove template-only README and AGENTS sections from the new project."""
    for relative in TEMPLATE_FILES:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        start = text.find(TEMPLATE_START)
        end = text.find(TEMPLATE_END)
        if start == -1 or end == -1 or end < start:
            continue
        text = text[:start] + text[end + len(TEMPLATE_END):]
        text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
        path.write_text(text, encoding="utf-8")


def apply_replacements(text, replacements):
    """Apply replacements simultaneously so new values are not rewritten."""
    tokens = []
    updated = text
    for index, (old, new) in enumerate(replacements):
        token = f"\x00{index}\x00"
        if token in text:
            fail("input already contains an internal replacement marker")
        tokens.append((token, new))
        if isinstance(old, re.Pattern):
            updated = old.sub(token, updated)
        else:
            updated = updated.replace(old, token)
    for token, new in tokens:
        updated = updated.replace(token, new)
    return updated


def replace_in_file(path, replacements):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    updated = apply_replacements(text, replacements)
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def build_renames(root, app_id, slug):
    """Return validated source/target paths for every identity-derived file."""
    renames = {
        Path("src/hello.in"): Path(f"src/{slug}.in"),
        Path("src/hello.gresource.xml"): Path(f"src/{slug}.gresource.xml"),
        Path("data/com.example.Hello.desktop.in"): Path(
            f"data/{app_id}.desktop.in"
        ),
        Path("data/com.example.Hello.metainfo.xml.in"): Path(
            f"data/{app_id}.metainfo.xml.in"
        ),
        Path("data/com.example.Hello.gschema.xml"): Path(
            f"data/{app_id}.gschema.xml"
        ),
        Path("data/com.example.Hello.service.in"): Path(
            f"data/{app_id}.service.in"
        ),
        Path("data/icons/hicolor/scalable/apps/com.example.Hello.svg"): Path(
            f"data/icons/hicolor/scalable/apps/{app_id}.svg"
        ),
        Path(
            "data/icons/hicolor/symbolic/apps/com.example.Hello-symbolic.svg"
        ): Path(f"data/icons/hicolor/symbolic/apps/{app_id}-symbolic.svg"),
        Path("com.example.Hello.json"): Path(f"{app_id}.json"),
    }

    target_names = set()
    source_names = set(renames)
    for old, new in renames.items():
        source = root / old
        target = root / new
        if not source.exists():
            fail(f"expected source file is missing: {old}")
        normalized = str(new).casefold()
        if normalized in target_names:
            fail(f"multiple template files map to the same target: {new}")
        target_names.add(normalized)
        if old != new and target.exists():
            fail(f"refusing to overwrite existing target: {new}")
        if new in source_names and new != old:
            fail(f"rename target is also a template source file: {new}")
    return renames


def main():
    parser = argparse.ArgumentParser(
        description="Rename the GTK Adwaita scaffold for a new application."
    )
    parser.add_argument(
        "--app-id",
        help="reverse-DNS app ID, e.g. com.example.MyApp or io.github.you.MyApp",
    )
    parser.add_argument("--name", help="human-readable application name")
    parser.add_argument("--slug", help="lowercase Python/gettext slug (default: derived from --name)")
    parser.add_argument("--author", help="author name")
    parser.add_argument("--author-email", help="author email")
    parser.add_argument(
        "--repo-url",
        help=(
            "project homepage or repository URL; code-hosting app IDs require "
            "the matching repository URL"
        ),
    )
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    main_py = ROOT / "src" / "main.py"
    if DEFAULT_APP_ID not in main_py.read_text(encoding="utf-8"):
        fail("this tree is already initialized (could not find the template app ID)")

    app_id = (args.app_id or ask("Application ID", DEFAULT_APP_ID)).strip()
    validate_app_id(app_id)

    name = (args.name or ask("Application name", DEFAULT_NAME)).strip()
    validate_text("application name", name)
    slug = (args.slug or slugify(name)).strip()
    validate_slug(slug)

    author = (args.author or ask("Author name", DEFAULT_AUTHOR)).strip()
    validate_text("author name", author)
    email = (args.author_email or ask("Author email", DEFAULT_EMAIL)).strip()
    validate_email(email)
    repo_url = (
        args.repo_url or ask("Repository URL", DEFAULT_URL)
    ).strip().rstrip("/")
    validate_url(repo_url)
    validate_repository_identity(app_id, repo_url)

    gtype = gtype_prefix(slug)
    app_id_path = "/" + app_id.replace(".", "/")
    developer_id = app_id.rsplit(".", 1)[0]

    replacements = [
        (DEFAULT_URL, repo_url),
        (f"{DEFAULT_SLUG.upper()}_DEBUG", f"{slug.upper()}_DEBUG"),
        (
            f"{DEFAULT_SLUG.upper()}_APPIMAGE_BUILD",
            f"{slug.upper()}_APPIMAGE_BUILD",
        ),
        (DEFAULT_APP_ID, app_id),
        ("/com/example/Hello", app_id_path),
        ('<developer id="com.example">', f'<developer id="{developer_id}">'),
        # GType identifiers: HelloApplication, HelloWindow, HelloFoo, ...
        (re.compile(r"\bHello(?=[A-Z])"), gtype),
        (DEFAULT_SLUG, slug),
        (DEFAULT_NAME, name),
        (DEFAULT_AUTHOR, author),
        (DEFAULT_EMAIL, email),
    ]

    renames = build_renames(ROOT, app_id, slug)

    print(f"Initializing {name}")
    print(f"  application ID: {app_id}")
    print(f"  slug:           {slug}")
    print(f"  GType prefix:   {gtype}")
    print(f"  author:         {author} <{email}>")
    print(f"  repository:     {repo_url}")
    print("Renaming:")
    for old, new in renames.items():
        print(f"  {old} -> {new}")

    if not args.yes:
        answer = input("Proceed? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("aborted")
            return 1

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if relative in SKIP_FILES:
            continue
        replace_in_file(path, replacements)

    for old, new in renames.items():
        if old == new:
            continue
        source = ROOT / old
        if not source.exists():
            fail(f"expected source file is missing: {old}")
        source.rename(ROOT / new)

    strip_template_sections()

    print(f"Done: {name} is ready. Run: meson setup build --prefix=\"$PWD/build-install\"")
    print(
        "The initializer is no longer needed; delete scripts/init.py and "
        "tests/test_init.py if you do not want to keep the template defaults "
        "in this project."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
