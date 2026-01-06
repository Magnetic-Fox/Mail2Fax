#!/usr/bin/env python3

# Simple (and temporary) image tools
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn!

import PIL.Image


# Very simple get image format (if possible) utility
def quickImageFormat(data):
	try:
		return PIL.Image.open(io.BytesIO(data)).format.lower()
	except:
		return ""

# Very quick and simple "if-we-have-an-image" test
def quickImageTest(data):
	return quickImageFormat(data) != ""
