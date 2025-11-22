#!/usr/bin/env python3

# TIFF tools utilizing paps, gs, convert, tiffset and Pillow (PIL)
#
# by Magnetic-Fox, 19.04.2025 - 22.11.2025
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

# Text to TIFF renderer (0 - standard resolution, 1 - fine resolution, 2 - super fine resolution)
#
# Default bottom margin value explanation:
# 141 PS points of bottom margin were chosen to achieve 2000 px height for image after cutting
# using cutter procedure (which has its default bottom margin set to 94 pixels).
#
# Why?
# 196 pixels per inch is the base document vertical resolution for G3 fax produced by GhostScript.
# 1 PostScript point is 1/72 inch, which means that 72 PostScript points gives us 196 pixels.
# Default page height for 196 DPI is 2289 pixels, which gives us 289 too much (we want 2000).
# Cutter utility needs additional 94 pixels to provide default bottom margin, so we need to add this too.
# Now: 289 + 94 (default from cutter) gives us 383 pixels we want out.
# This gives us such formula: bottomMargin = (72 * 383) / 196, which we have to ceil (to not exceed 2000 pixels!)
#
# Why 2000 pixels?
# That's because mgetty-fax will automatically scale images that exceeds such height.
# I just wanted to avoid it. ;)
def textToTIFF(tiffFileName, textData, resolution = 1, fontNameAndSize = "Monospace 10", topMargin = 6, bottomMargin = 141):
	# Prepare paps and gs commands
	papsCommand = ["paps", "--font=" + fontNameAndSize, "--top-margin=" + str(topMargin), "--bottom-margin=" + str(bottomMargin)]
	ghscCommand = ["gs", "-sDEVICE=tiffg3"]

	# Standard resolution
	if resolution == 0:
		ghscCommand += ["-r204x98"]

	# Super fine resolution
	elif resolution == 2:
		ghscCommand += ["-r204x391"]

	# Fine resolution ("normal")
	else:
		ghscCommand += ["-r204x196"]

	ghscCommand += ["-sOutputFile=" + tiffFileName, "-dBATCH", "-dNOPAUSE", "-dSAFER", "-dQUIET", "-"]

	# Create processes
	paps = subprocess.Popen(papsCommand, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
	ghsc = subprocess.Popen(ghscCommand, stdin = subprocess.PIPE)

	# Pass text (encoded to the bytes type) to paps command and pass got postscript to gs command
	postScript = paps.communicate(textData.encode())[0]
	ghsc.communicate(postScript)

	return

# Text file to TIFF renderer (wrapper)
def textFileToTIFF(tiffFileName, textFileName, resolution = 1, fontNameAndSize = "Monospace 10", topMargin = 6, bottomMargin = 141):
	textFile = open(textFileName, "r")
	textToTIFF(tiffFileName, textFile.read(), resolution, fontNameAndSize, topMargin, bottomMargin)
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
