#!/usr/bin/env python3

# Additional tools and classes
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn!


# Settings class (with default settings applied)
class Settings:
	SETTINGS_FILE = "settings.ini"
	SETTINGS_RELOADED = False
	NO_DATA = "(no data)"
	SENDER = "Sender:  "
	SUBJECT = "Subject: "
	DATE = "Date:    "
	PHONE_NUMBER = ""       # well, string-like variable is best choice for phone numbers
	DELETE_SUBJECT_TRIGGER = True
	DELETE_MESSAGE_TRIGGER = True
	SUBJECT_TRIGGER = "[FAX] "
	MESSAGE_TRIGGER = "!DISCARD!"
	STANDARD_TRIGGER = "!STANDARD!"
	USE_STANDARD_TRIGGER = True
	DELETE_STANDARD_TRIGGER = True
	USE_PLAIN = True
	MSPACES_TONL = False
	AMPS_CHANGE = False
	DEFAULT_SETTINGS = "FAX"
	USE_DEFAULT_SETTINGS_ON_WRONG_PARAM = False
	STRIP_BE_NLS = True
	STRIP_INTEXT_NLS = True
	DEFAULT_LOGGER_ADDRESS = "/dev/log"
	ROUTE_TO_FAX = ""
	TEXT_FONT_NAME = "Monospace"
	TEXT_FONT_SIZE = 10
	TEXT_TOP_MARGIN = 6
	DATE_TIMEZONE = ""      # will be interpreted as local timezone
	DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
	LOG_MESSAGE_TO_FILE = True
	MESSAGE_LOG_FILE = "/var/log/Mail2Fax/mails.gz"
	UNPACK_MULTI_TIFF = True


# Old codes to be removed in future:

# Procedure grouping plain-text and non-plain-text parts of the message (indexed output)
def groupTypesIndexes(parts, plainInt, nonPlInt):
	index = 0
	for test in parts:
		if "text" in test.get_content_type():
			if "plain" in test.get_content_type():
				plainInt += [index]
			else:
				nonPlInt += [index]
		index += 1
	return

# Procedure removing indexes depending on "use plain text" setting
def plainAndHTMLDecision(parts, plainInt, nonPlInt):
	if Settings.USE_PLAIN:
		if plainInt != []:
			for i in reversed(nonPlInt):
				parts.pop(i)
	else:
		if nonPlInt != []:
			for i in reversed(plainInt):
				parts.pop(i)
	return

# Binding procedure for plain or non-plain decision
def decidePlainOrHTML(parts):
	plainInt = []
	nonPlInt = []
	groupTypesIndexes(parts, plainInt, nonPlInt)
	plainAndHTMLDecision(parts, plainInt, nonPlInt)
	return
