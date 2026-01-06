#!/usr/bin/env python3

# Data tools
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn!

import subprocess


# Function for determining attachment's mime type (using file command)
def determineMimeType(data):
	fileCommand = ["file", "-b", "--mime-type", "-"]
	fileProcess = subprocess.Popen(fileCommand, stdin = subprocess.PIPE, stdout = subprocess.PIPE)

	if isinstance(data, str):
		data = data.encode()

	return fileProcess.communicate(data)[0].decode().rstrip()

# Simple main type extractor from mime type got from file command
def getMainType(mimeType):
	return mimeType.split("/")[0]

# Simple sub type extractor from mime type got from file command
def getSubType(mimeType):
	return "".join(mimeType.split("/")[1:])
