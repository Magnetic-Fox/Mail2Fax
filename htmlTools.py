#!/usr/bin/env python3

# HTML tools for converting HTML to plain text
#
# by Magnetic-Fox, 13.07.2024 - 12.04.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn

import html.parser


# Great HTML to text part found on Stack Overflow
class HTMLFilter(html.parser.HTMLParser):
	text = ""

	def handle_data(self, data):
		self.text += data

# Simple HTML to plain text converter
def HTMLToText(inputData):
	# Replace any <br> and <br /> (in all cases) to the new lines, because this simple HTMLFilter can't do this automatically
	inputData = inputData.replace("<br>", "\n").replace("<br />", "\n")
	inputData = inputData.replace("<Br>", "\n").replace("<Br />", "\n")
	inputData = inputData.replace("<bR>", "\n").replace("<bR />", "\n")
	inputData = inputData.replace("<BR>", "\n").replace("<BR />", "\n")

	# Temporary variable for start position of <br ... > searching
	posStart = 0

	# Loop for searching strange <br ... > constructions...
	while (inputData.find("<br ", posStart) != -1) or (inputData.find("<Br ", posStart) != -1) or (inputData.find("<bR ", posStart) != -1) or (inputData.find("<BR ", posStart) != -1):
		posStart = inputData.find("<br ")
		if posStart == -1:
			posStart = inputData.find("<Br ")
			if posStart == -1:
				posStart = inputData.find("<bR ")
				if posStart == -1:
					posStart = inputData.find("<BR ")

		# Search end position
		endPos = inputData.find(">", posStart)

		if endPos != -1:
			# Replace all occurences and move to the beginning of the data
			inputData = inputData.replace(inputData[posStart:endPos + 1], "\n")
			posStart = 0
		else:
			# If '>' not found - move one character next to avoid inifite loop
			posStart += 1

	# Prepare converter and feed it with input data
	converter = HTMLFilter()
	converter.feed(inputData)

	# Return automatically converted text
	return converter.text
