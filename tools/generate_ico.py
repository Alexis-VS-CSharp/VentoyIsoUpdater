"""
Convertit assets/icon.png en assets/icon.ico (multi-résolution).
À exécuter une fois avant le build Windows :
    python tools/generate_ico.py
"""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src  = os.path.join(BASE, "assets", "icon.png")
dst  = os.path.join(BASE, "assets", "icon.ico")

img = Image.open(src).convert("RGBA")
# ICO multi-résolution : 16, 32, 48, 64, 128, 256
sizes = [(s, s) for s in (16, 32, 48, 64, 128, 256)]
img.save(dst, format="ICO", sizes=sizes)
print(f"Généré : {dst}")
