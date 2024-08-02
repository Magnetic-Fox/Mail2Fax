#!/usr/bin/env python3

# Very simple image rotating utility (landscape -> portrait)
#
# by Magnetic-Fox, 02.08.2024
#
# (C)2024 Bartłomiej "Magnetic-Fox" Węgrzyn!

import PIL.Image
import sys

def isLandscape(image):
	return image.width>image.height

def rotate90(image):
	return image.rotate(90,expand=1)

def rotateIfNecessary(image):
	if isLandscape(image):
		return rotate90(image)
	else:
		return image

def loadAndRotateIfNecessary(filename):
	img=PIL.Image.open(filename)
	if isLandscape(img):
		img=rotate90(img)
		img.save(filename)
	return

# Main code goes here...

if __name__ == "__main__":
	if len(sys.argv)==2:
		loadAndRotateIfNecessary(sys.argv[1])
	else:
		exit(1)
