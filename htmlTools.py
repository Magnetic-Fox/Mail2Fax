#!/usr/bin/env python3

# HTML tools for converting HTML to plain text
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
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
	# Replace any <br> and <br /> to the new lines, because this simple HTMLFilter can't do this automatically
	inputData = inputData.replace("<br>", "\n").replace("<br />", "\n")

	# Prepare converter and feed it with input data
	converter = HTMLFilter()
	converter.feed(inputData)

	# Return automatically converted text
	return converter.text
