# there should be no issues importing sqlite libraries
import sqlite3
from packaging import version
# Ensure we haven't inadvertently got the (ancient) system SQLite
sqlite_version = version.parse(sqlite3.sqlite_version)
assert version.parse('3.17.0') <= sqlite_version, f'Current version is {sqlite_version}'
sqlite3.connect(":memory:")

# pyenv has trouble building the tkinter extension, so checking for that
# this tends to happen on macos, where even the exception handling below
# will error out as _tkinter is not present
# On Linux, the import can fail because DISPLAY is not set. In this case
# a TclError is raised. But if we have that, we're good to go.
try:
    import tkinter
except _tkinter.TclError:
    print("no display, but that's ok")

print('python interpreter smoke test ok')
