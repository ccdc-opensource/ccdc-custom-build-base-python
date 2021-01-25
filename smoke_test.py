import platform

# there should be no issues importing sqlite libraries
import sqlite3

# pyenv has trouble building the tkinter extension, so checking for that
# this tends to happen on macos, where even the exception handling below
# will error out as _tkinter is not present
# On Linux, the import can fail because DISPLAY is not set. In this case
# a TclError is raised. But if we have that, we're good to go.
try:
    import tkinter
    print('ok')
except _tkinter.TclError:
    print("no display, but that's ok")
