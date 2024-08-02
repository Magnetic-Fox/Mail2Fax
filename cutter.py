#!/usr/bin/env python3

# Simple bottom cutter for G3 TIFFs created by PAPS + Ghostscript
#
# by Magnetic-Fox, 02.08.2024
#
# (C)2024 Bartłomiej "Magnetic-Fox" Węgrzyn!

import PIL.Image
import sys

# default
leave=94

def checkLine(image, pixels, lineNumber):
	for i in range(image.width):
		if pixels[i,lineNumber] != 255:
			return False
	return True

def bottomEnd(image, pixels):
	for i in range(image.height):
		if not checkLine(image,pixels,image.height-i-1):
			return image.height-i-1
	return -1

def cuttingPossibleFormula(botEnd, imgHeight, leave=leave):
	return (botEnd!=-1) and (botEnd+leave<imgHeight)

def cuttingPossible(image, pixels, leave=leave):
	botEnd=bottomEnd(image,pixels)
	return cuttingPossibleFormula(botEnd,image.height,leave)

def cutBottom(image, pixels, leave=leave):
	botEnd=bottomEnd(image,pixels)
	if cuttingPossibleFormula(botEnd,image.height,leave):
		return image.crop((0,0,image.width,botEnd+leave))
	else:
		return None

def setLeave(newLeave):
	global leave
	leave=newLeave
	return

def getLeave():
	global leave
	return leave

def loadAndCrop(filename):
	img=PIL.Image.open(filename)
	pxl=img.load()
	img=cutBottom(img,pxl)
	img.save(filename)
	return

# Main code goes here

if __name__ == "__main__":
	if len(sys.argv)==2:
		loadAndCrop(sys.argv[1])
	else:
		exit(1)
