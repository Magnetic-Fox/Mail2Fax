#!/usr/bin/env python3

# Mail tools
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn!

import dateutil
import email.header


# Mail header decoding helper
def decodeHeader(input):
	output = ""

	if input != None:
		parts = email.header.decode_header(input)
		for part in parts:
			if part[1] == None:
				encoding = "ascii"
			else:
				encoding = part[1]

			try:
				output += str(part[0], encoding)
			except:
				output += part[0]

	# If output is nothing then set it to None
	if output == "":
		output = None

	# Return output
	return output

# Simple and good utility to make date/time more readable and to deal
# with timezones if possible (by default, relatively to the local machine's timezone)
def mailDateToFormat(date, timezone = "", format = "%Y-%m-%d %H:%M:%S"):
	try:
		return dateutil.parser.parse(date).astimezone(dateutil.tz.gettz(timezone)).strftime(format)
	except:
		return date

# Try..Except version of decodeHeader() function with returning None on empty strings
def tryDecodeHeader(header):
	try:
		return decodeHeader(header)
	except:
		return None
