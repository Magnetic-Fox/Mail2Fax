#!/usr/bin/env python3

# Simple bottom cutter for G3 TIFFs utilizing PIL and ImageMagick
#
# by Magnetic-Fox, 02.08.2024 - 22.11.2025
#
# (C)2024-2025 Bartłomiej "Magnetic-Fox" Węgrzyn!

import sys
import math
import subprocess
import PIL.Image


# Default bottom margin size (in pixels)
DEFAULT_LEAVE = 94


# Line checker
def checkLine(image, pixels, lineNumber):
	for i in range(image.width):
		if pixels[i, lineNumber] != 255:
			return False
	return True

# Bottom end finder
def bottomEnd(image, pixels):
	for i in range(image.height):
		if not checkLine(image, pixels, image.height - i - 1):
			return image.height - i - 1
	return -1

# Cutting possible formula
def cuttingPossibleFormula(botEnd, imgHeight, leave = DEFAULT_LEAVE):
	return (botEnd != -1) and (botEnd + leave < imgHeight)

# Cutting possible formula on image wrapper
def cuttingPossible(image, pixels, leave = DEFAULT_LEAVE):
	botEnd = bottomEnd(image, pixels)
	return cuttingPossibleFormula(botEnd, image.height, leave)

# Bottom cut position finder
def bottomCutPosition(image, pixels, leave = DEFAULT_LEAVE):
	botEnd = bottomEnd(image, pixels)
	if cuttingPossibleFormula(botEnd, image.height, leave):
		return botEnd + leave
	else:
		return None

# Load and crop all-in-one solution (which should be named loadAndCutBottom, but...)
def loadAndCrop(filename, leave = DEFAULT_LEAVE):
	# PIL part
	img = PIL.Image.open(filename)
	pxl = img.load()
	cuttingPosition = bottomCutPosition(img, pxl, leave)
	img.close()

	# ImageMagick part
	if cuttingPosition != None:
		convertCommand = ["convert", filename, "-crop", "x" + str(cuttingPosition) + "+0+0", filename]
		return subprocess.run(convertCommand).returncode

	return 0

# Simple bottom cut calculating function (0 - standard resolution, 1 - fine resolution (default), 2 - super fine resolution)
def calculateCutMargin(resolution, leave = DEFAULT_LEAVE):
	if resolution == 0:
		output = leave / 2

	elif resolution == 2:
		output = leave * 2

	else:
		output = leave

	return math.ceil(output)


# Autorun part (for standalone use)
if __name__ == "__main__":
	exitCode = 0

	try:
		if len(sys.argv) == 2:
			exitCode = loadAndCrop(sys.argv[1])
		elif len(sys.argv) == 3:
			exitCode = loadAndCrop(sys.argv[1], int(sys.argv[2]))
		else:
			print("Usage: cutter.py <filename> [bottomMarginSize]")
			exitCode = 1
	except:
		exitCode = 2

	# Return exit code
	exit(exitCode)
