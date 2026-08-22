"""
Converts assets/icon.png to assets/icon.ico (multi-resolution).
Run once before the Windows build:
    python tools/generate_ico.py
"""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src  = os.path.join(BASE, "assets", "icon.png")
dst  = os.path.join(BASE, "assets", "icon.ico")

img = Image.open(src).convert("RGBA")
# Multi-resolution ICO: 16, 32, 48, 64, 128, 256
sizes = [(s, s) for s in (16, 32, 48, 64, 128, 256)]
img.save(dst, format="ICO", sizes=sizes)
print(f"Generated: {dst}")
