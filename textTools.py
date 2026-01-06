#!/usr/bin/env python3

# Text tools (for better experience on plain text)
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn!

import htmlTools


# Simple new line characters counter
def countNewLines(data, position):
	count = 0

	while data.find("\n", position) == position:
		count = count + 1
		position = position + 1

	return count

# Simple duplicated new line characters remover
def removeDuplicatedNewLines(data):
	while data.find("\n\n\n") != -1:
		count = countNewLines(data, data.find("\n\n\n"))
		data = data.replace("\n" * count, "\n\n")

	return data

# Simple spaces counter
def spacesCount(string, position):
	for x in range(position, len(string)):
		if(string[x] != ' '):
			return x - position

	if(position <= len(string)):
		return len(string) - position

	else:
		return 0

# Multi spaces to returns
def multiSpacesToReturns(string):
	while(string.find("  ") != -1):
		# Not really optimized line, but I didn't want to use regexes ;)
		string = string.replace(" " * spacesCount(string, string.find("  ")), "\n" * (spacesCount(string, string.find("  ")) - 1), 1)

	return string

# Function for finding HTML-style amp character
def findAmpChar(string, position = 0):
	ampPos=string.find('&', position)
	endPos=string.find(';', ampPos)

	if endPos > ampPos:
		return string[ampPos:endPos+1]
	else:
		return ""

# Function for changing all HTML-style amp characters
def changeAmpChars(string):
	position = 0

	while(findAmpChar(string, position) != ""):
		converter = htmlTools.HTMLFilter()
		converter.feed(findAmpChar(string))
		string = string.replace(findAmpChar(string), converter.text)
		position = string.find("&", position + 1)

		if position < 0:
			break

	return string
