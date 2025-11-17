#!/usr/bin/env python3

# TIFF tools utilizing paps, gs, convert, tiffset and Pillow (PIL)
#
# by Magnetic-Fox, 19.04.2025 - 17.11.2025
#
# (C)2025 Bartłomiej "Magnetic-Fox" Węgrzyn


import subprocess
import PIL.Image


# Image to non-G3 TIFF file converter
def imageToTIFF(imageFileName, tiffFileName, pageWidth = 1728, marginLeft = 32, marginRight = 32):
	# Get image size to test if image has to be rotated
	img = PIL.Image.open(imageFileName)
	width, height = img.size
	img.close()

	# Prepare command
	command = ["convert", imageFileName]

	# Set to rotate if needed
	if width > height:
		command += ["-rotate", "90"]

	# Below should give such result for resize: 1664x
	command += ["-resize", str(pageWidth - marginLeft - marginRight) + "x"]
	command += ["-background", "white", "-gravity", "northwest", "-splice", str(marginLeft) + "x0"]
	command += ["-background", "white", "-gravity", "northeast", "-splice", str(marginRight) + "x0"]
	command += [tiffFileName]

	# Convert images to TIFFs with auto-size and auto-margin
	subprocess.run(command)

	return

# Text to TIFF renderer
def textToTIFF(tiffFileName, textData, fontName = "Monospace 10", topMargin = 6):
	# Prepare paps and gs commands
	papsCommand = ["paps", "--font=" + fontName, "--top-margin=" + str(topMargin)]
	ghscCommand = ["gs", "-sDEVICE=tiffg3", "-sOutputFile=" + tiffFileName, "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET", "-"]

	# Create processes
	paps = subprocess.Popen(papsCommand, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
	ghsc = subprocess.Popen(ghscCommand, stdin = subprocess.PIPE)

	# Pass text (encoded to the bytes type) to paps command and pass got postscript to gs command
	postScript = paps.communicate(textData.encode())[0]
	ghsc.communicate(postScript)

	return

# Text file to TIFF renderer (wrapper)
def textFileToTIFF(tiffFileName, textFileName, fontName = "Monospace 10", topMargin = 6):
	textFile = open(textFileName, "r")
	textToTIFF(tiffFileName, textFile.read(), fontName, topMargin)
	textFile.close()
	return

# Resizer and DPI information applier (0 - standard resolution, 1 - fine resolution, 2 - super fine resolution)
def resizeAndApplyResolution(tiffFileName, resolution):
	# Prepare main convert and tiffset commands
	convertCommand = ["convert", tiffFileName]
	tiffSetCommand = ["tiffset", "-s", "283"]

	# Standard resolution - shrink image vertically (0.5x) and set vertical DPI to 98
	if resolution == 0:
		convertCommand += ["-resize", "100%x50%"]
		tiffSetCommand += ["98.0"]

	# Fine resolution - no resize, but set vertical DPI to 196
	elif resolution == 1:
		# Resizing not needed, so no convert command
		tiffSetCommand += ["196.0"]

	# Super fine resolution - enlarge image vertically (2x) and set vertival DPI to 391
	elif resolution == 2:
		convertCommand += ["-resize", "200%x200%", "-resize", "50%x100%"]
		tiffSetCommand += ["391.0"]

	# On other resolution switch, raise an exception
	else:
		raise Exception("Wrong resolution switch!")

	# Add TIFF file name to the both commands
	convertCommand += [tiffFileName]
	tiffSetCommand += [tiffFileName]

	# Additional tiffsets before the main part (make space for DPI information and set horizontal DPI to 204)
	subprocess.run(["tiffset", "-s", "296", "2", tiffFileName])
	subprocess.run(["tiffset", "-s", "282", "204.0", tiffFileName])

	# Resize TIFF
	if resolution != 1:
		subprocess.run(convertCommand)

	# Apply vertical DPI information
	subprocess.run(tiffSetCommand)

	return
