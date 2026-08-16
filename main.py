#!/usr/bin/env python3
"""
VentoyIsoUpdater — Point d'entrée principal
"""

import sys
import os

# Permet d'importer les modules depuis la racine du projet,
# que ce soit en dev ou en exécutable PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from gui.app import VentoyIsoUpdaterApp
from gui import i18n
import core.preferences as prefs


def main():
    # Doit être fait avant toute construction de widget : tous les textes de
    # l'UI sont écrits en français dans le code et passent par gui.i18n.t()
    # pour être traduits à la volée si la langue active n'est pas "fr".
    i18n.set_language(prefs.get("language"))

    app = VentoyIsoUpdaterApp()

    # Icône dans la taskbar / gestionnaire de fenêtres
    icon_path = os.path.join(BASE_DIR, "assets", "icon.png")
    if os.path.isfile(icon_path):
        try:
            from PIL import Image, ImageTk
            _img   = Image.open(icon_path).convert("RGBA")
            _photo = ImageTk.PhotoImage(_img)
            app.wm_iconphoto(True, _photo)
            app._icon_ref = _photo   # empêche le garbage collector de libérer la référence
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
