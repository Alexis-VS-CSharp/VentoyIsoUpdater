#!/usr/bin/env python3
"""
VentoyIsoUpdater — main entry point
"""

import sys
import os

# Allows importing modules from the project root,
# whether running in dev or as a PyInstaller executable
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from gui.app import VentoyIsoUpdaterApp
from gui import i18n
import core.preferences as prefs


def main():
    # Must happen before any widget is built: every UI string is written
    # in French in the code and goes through gui.i18n.t() to be translated
    # on the fly if the active language isn't "fr".
    i18n.set_language(prefs.get("language"))

    app = VentoyIsoUpdaterApp()

    # Icon in the taskbar / window manager
    icon_path = os.path.join(BASE_DIR, "assets", "icon.png")
    if os.path.isfile(icon_path):
        try:
            from PIL import Image, ImageTk
            _img   = Image.open(icon_path).convert("RGBA")
            _photo = ImageTk.PhotoImage(_img)
            app.wm_iconphoto(True, _photo)
            app._icon_ref = _photo   # prevents the garbage collector from freeing the reference
        except Exception:
            try:
                import tkinter as tk
                _photo = tk.PhotoImage(file=icon_path)
                app.wm_iconphoto(True, _photo)
                app._icon_ref = _photo
            except Exception:
                pass

    app.mainloop()


if __name__ == "__main__":
    main()
