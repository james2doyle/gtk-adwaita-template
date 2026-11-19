"""Headless tests for the template initializer helpers."""

import contextlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SOURCE_ROOT)

spec = importlib.util.spec_from_file_location(
    "template_init", os.path.join(SOURCE_ROOT, "scripts", "init.py")
)
assert spec is not None and spec.loader is not None
template_init = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_init)

assert template_init.slugify("My App") == "my_app"
assert template_init.slugify("Hello") == "hello"
assert template_init.slugify("123 App") == "_123_app"
assert template_init.gtype_prefix("my_app") == "MyApp"
assert template_init.gtype_prefix("md_split") == "MdSplit"

template_init.validate_app_id("com.example.MyApp")
for bad_app_id in ("com.example", "invalid", "com.example."):
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            template_init.validate_app_id(bad_app_id)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"accepted invalid app ID: {bad_app_id}")


def expect_failure(function, *args):
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            function(*args)
        except SystemExit:
            return
    raise AssertionError(f"accepted invalid input for {function.__name__}: {args}")


expect_failure(template_init.validate_slug, "_")
template_init.validate_text("name", "My App")
for bad_name in ('Bad " Name', "Bad & Name", "Bad <Name", "Line\nBreak"):
    expect_failure(template_init.validate_text, "name", bad_name)

template_init.validate_email("me@example.com")
for bad_email in ("missing-at.example.com", "me@localhost", "me @@example.com"):
    expect_failure(template_init.validate_email, bad_email)

template_init.validate_url("https://github.com/example/app")
for bad_url in (
    "file:///tmp/app",
    "https://user:" + "secret" + "@example.com/app",
    "https://example.com/my app",
    "https://example.com/app?x=1&y=2",
):
    expect_failure(template_init.validate_url, bad_url)

# Replacements must be simultaneous: the new app ID contains "Hello", but the
# name/GType replacements must not modify the newly inserted identifier.
simultaneous = template_init.apply_replacements(
    "com.example.Hello HelloApplication",
    [
        (template_init.DEFAULT_APP_ID, "com.example.HelloApp"),
        (re.compile(r"\bHello(?=[A-Z])"), "MyApp"),
        (template_init.DEFAULT_NAME, "New Name"),
    ],
)
assert simultaneous == "com.example.HelloApp MyAppApplication", simultaneous

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    sample = root / "sample.txt"
    sample.write_text("Hello hello", encoding="utf-8")
    template_init.replace_in_file(
        sample,
        [("Hello", "World"), ("hello", "world")],
    )
    assert sample.read_text(encoding="utf-8") == "World world"

    readme = root / "README.md"
    readme.write_text(
        "before\n"
        "<!-- template:start -->\n"
        "template only\n"
        "<!-- template:end -->\n"
        "after\n",
        encoding="utf-8",
    )
    agents = root / "AGENTS.md"
    agents.write_text(
        "before\n"
        "<!-- template:start -->\n"
        "template only\n"
        "<!-- template:end -->\n"
        "after\n",
        encoding="utf-8",
    )
    original_root = template_init.ROOT
    setattr(template_init, "ROOT", root)
    try:
        template_init.strip_template_sections()
    finally:
        setattr(template_init, "ROOT", original_root)
    stripped = readme.read_text(encoding="utf-8")
    assert "template:start" not in stripped
    assert "template only" not in stripped
    assert "before" in stripped and "after" in stripped
    stripped_agents = agents.read_text(encoding="utf-8")
    assert "template:start" not in stripped_agents
    assert "template only" not in stripped_agents
    assert "before" in stripped_agents and "after" in stripped_agents

# End-to-end initialization, including identifiers that contain template text.
main_path = Path(SOURCE_ROOT) / "src/main.py"
if template_init.DEFAULT_APP_ID in main_path.read_text(encoding="utf-8"):
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp) / "Hello Tools"
        shutil.copytree(
            SOURCE_ROOT,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                ".delta",
                "build",
                "build-install",
                "build-flatpak",
                "build-appimage",
                "AppDir",
                "appimage-build",
                "squashfs-root",
                "*.AppImage",
                ".bundle.yml",
                ".flatpak-builder",
                ".dex",
                ".ruff_cache",
                "dist",
                "__pycache__",
                "*.pyc",
            ),
        )
        command = [
            sys.executable,
            str(destination / "scripts/init.py"),
            "--yes",
            "--app-id",
            "com.acme.HelloApp",
            "--name",
            "Hello Tools",
            "--author",
            "Template User",
            "--author-email",
            "user@example.com",
            "--repo-url",
            "https://github.com/example/hello-tools",
        ]
        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": tmp,
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        collision = destination / "data/com.acme.HelloApp.desktop.in"
        collision.write_text("must not be overwritten", encoding="utf-8")
        blocked = subprocess.run(
            command,
            cwd=destination,
            env=clean_env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert blocked.returncode == 1
        assert "refusing to overwrite" in blocked.stderr
        assert template_init.DEFAULT_APP_ID in (
            destination / "src/main.py"
        ).read_text(encoding="utf-8")
        collision.unlink()

        result = subprocess.run(
            command,
            cwd=destination,
            env=clean_env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        main_text = (destination / "src/main.py").read_text(encoding="utf-8")
        assert "com.acme.HelloApp" in main_text
        assert "HelloToolsApplication" in main_text
        assert "com.example.Hello" not in main_text
        assert "HELLO_TOOLS_DEBUG" in main_text
        assert "HELLO_DEBUG" not in main_text
        appimage_text = (destination / "scripts/build-appimage.sh").read_text(
            encoding="utf-8"
        )
        assert "HELLO_TOOLS_APPIMAGE_BUILD" in appimage_text
        assert "HELLO_APPIMAGE_BUILD" not in appimage_text
        agents_text = (destination / "AGENTS.md").read_text(encoding="utf-8")
        assert "Template initialization" not in agents_text
        assert "template:start" not in agents_text
        assert (destination / "src/hello_tools.in").is_file()
        assert (destination / "data/com.acme.HelloApp.desktop.in").is_file()
        assert (destination / "com.acme.HelloApp.json").is_file()
        assert not (destination / "src/hello.in").exists()
        assert "template:start" not in (
            destination / "README.md"
        ).read_text(encoding="utf-8")

        second = subprocess.run(
            [sys.executable, str(destination / "scripts/init.py"), "--yes"],
            cwd=destination,
            env=clean_env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert second.returncode == 1
        assert "already initialized" in second.stderr

print("ok: initializer helpers")
