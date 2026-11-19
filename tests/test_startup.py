"""Guard the lazy startup boundary.

Importing the application module must not import the GTK window module. The
check runs in a fresh subprocess so an earlier test cannot populate
``sys.modules``.
"""

import os
import subprocess
import sys

SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHECK = """
import sys
import src.main

assert "src.window" not in sys.modules, "src.main imported the window eagerly"
print("ok: src.window was not imported")
"""

env = os.environ.copy()
env["PYTHONPATH"] = SOURCE_ROOT
env["PYTHONDONTWRITEBYTECODE"] = "1"

result = subprocess.run(
    [sys.executable, "-c", CHECK],
    cwd=SOURCE_ROOT,
    env=env,
    capture_output=True,
    text=True,
    check=False,
)
if result.returncode != 0:
    sys.stderr.write(result.stdout)
    sys.stderr.write(result.stderr)
    raise SystemExit(result.returncode)

print("ok: lazy startup imports")
