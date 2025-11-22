#!/usr/bin/env python3

# E-Mail to Fax Relay Utility for Procmail and MGetty-Fax (faxspool)
#
# Using PAPS, GhostScript, ImageMagick (convert), Pillow (PIL),
# file command and system logger (logger; now via Python modules)
#
# Software intended for use on Linux systems (especially Debian)
# because of calling conventions and specific system utilities used
#
# by Magnetic-Fox, 13.07.2024 - 23.11.2025
#
# (C)2024-2025 Bartłomiej "Magnetic-Fox" Węgrzyn!


import tempfile
import sys
import os
import subprocess
import base64
import dateutil
import datetime
import configparser
import io
import gzip
import mimetypes
import logging
import logging.handlers
import email
import email.header
import email.quoprimime
import html.parser
import PIL.Image
import StringTable
import cutter
import tiffTools


# Global variable for logger (to be replaced by logging class someday...)
preparedLogger = None

# Static settings class (with default settings applied)
class Settings:
	SETTINGS_FILE = "settings.ini"
	SETTINGS_RELOADED = False
	NO_DATA = "(no data)"
	SENDER = "Sender:  "
	SUBJECT = "Subject: "
	DATE = "Date:    "
	PHONE_NUMBER = ""	# well, string-like variable is best choice for phone numbers
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
	DATE_TIMEZONE = ""	# will be interpreted as local timezone
	DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
	LOG_MESSAGE_TO_FILE = True
	MESSAGE_LOG_FILE = "/var/log/Mail2Fax/mails.gz"
	UNPACK_MULTI_TIFF = True

# Great HTML to text part found on Stack Overflow
class HTMLFilter(html.parser.HTMLParser):
	text = ""

	def handle_data(self, data):
		self.text += data

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

# Simple procedure for preparing system logger to use globally in this script (to be changed to the logging class someday...)
def prepareGlobalLogger():
	global preparedLogger

	if preparedLogger == None:
		preparedLogger = prepareLogger(loggerAddress = Settings.DEFAULT_LOGGER_ADDRESS)

	return

# Simple logger preparation function
def prepareLogger(loggerName = __name__, loggerAddress = Settings.DEFAULT_LOGGER_ADDRESS):
	logger = logging.getLogger(loggerName)
	handler = logging.handlers.SysLogHandler(address = loggerAddress)

	logger.setLevel(logging.INFO)
	logger.addHandler(handler)

	return logger

# Simple logging utility
def logInfo(message, logger = None, prefix = ""):
	if None:
		raise Exception("No logger selected!")

	logger.info(prefix + message)

	return

# Simple procedure for passing error messages to the system log
def logError(errorString):
	logInfo(logger = preparedLogger, prefix = StringTable.LOGGER_ERROR, message = errorString)
	return

# Simple procedure for passing warnings to the system log
def logWarning(warningString):
	logInfo(logger = preparedLogger, prefix = StringTable.LOGGER_WARNING, message = warningString)
	return

# Simple procedure for passing notices to the system log
def logNotice(noticeString):
	logInfo(logger = preparedLogger, prefix = StringTable.LOGGER_NOTICE, message = noticeString)
	return

# Procedure for loading settings from the INI file
def loadSettings(whichFax = "", settingsFile = Settings.SETTINGS_FILE):
	config = configparser.ConfigParser(interpolation = None)

	if config.read(settingsFile) == []:
		try:
			# Try finding file in the script's path
			settingsFile = os.path.dirname(os.path.realpath(__file__)) + "/" + settingsFile
			config.read(settingsFile)

		except:
			pass

	# Load main settings if possible (or defaults, if not)

	# Header strings
	Settings.NO_DATA = config.get("strings", "no_data", fallback = Settings.NO_DATA).replace('"', '')
	Settings.SENDER = config.get("strings", "sender", fallback = Settings.SENDER).replace('"', '')
	Settings.SUBJECT = config.get("strings", "subject", fallback = Settings.SUBJECT).replace('"', '')
	Settings.DATE = config.get("strings", "date", fallback = Settings.DATE).replace('"', '')

	# Message settings
	Settings.MESSAGE_TRIGGER = config.get("message", "message_trigger", fallback = Settings.MESSAGE_TRIGGER).replace('"', '')
	Settings.STANDARD_TRIGGER = config.get("message", "standard_trigger", fallback = Settings.STANDARD_TRIGGER).replace('"', '')
	Settings.DELETE_SUBJECT_TRIGGER = config.getboolean("message", "delete_subject_trigger", fallback = Settings.DELETE_SUBJECT_TRIGGER)
	Settings.DELETE_MESSAGE_TRIGGER = config.getboolean("message", "delete_message_trigger", fallback = Settings.DELETE_MESSAGE_TRIGGER)
	Settings.DELETE_STANDARD_TRIGGER = config.getboolean("message", "delete_standard_trigger", fallback = Settings.DELETE_STANDARD_TRIGGER)
	Settings.USE_STANDARD_TRIGGER = config.getboolean("message", "use_standard_trigger", fallback = Settings.USE_STANDARD_TRIGGER)
	Settings.USE_PLAIN = config.getboolean("message", "use_plain", fallback = Settings.USE_PLAIN)
	Settings.MSPACES_TONL = config.getboolean("message", "multispaces_to_new_lines", fallback = Settings.MSPACES_TONL)
	Settings.AMPS_CHANGE = config.getboolean("message", "convert_amp_characters", fallback = Settings.AMPS_CHANGE)
	Settings.STRIP_BE_NLS = config.getboolean("message", "strip_new_lines_on_startend", fallback = Settings.STRIP_BE_NLS)
	Settings.STRIP_INTEXT_NLS = config.getboolean("message", "strip_intext_new_lines", fallback = Settings.STRIP_INTEXT_NLS)

	# Logger settings
	Settings.DEFAULT_LOGGER_ADDRESS = config.get("logger", "address", fallback = Settings.DEFAULT_LOGGER_ADDRESS).replace('"', '')

	# Rendering settings
	Settings.TEXT_FONT_NAME = config.get("rendering", "text_font_name", fallback = Settings.TEXT_FONT_NAME).replace('"', '')
	Settings.TEXT_FONT_SIZE = config.getint("rendering", "text_font_size", fallback = Settings.TEXT_FONT_SIZE)
	Settings.TEXT_TOP_MARGIN = config.getint("rendering", "text_top_margin", fallback = Settings.TEXT_TOP_MARGIN)

	# Default settings
	Settings.DEFAULT_SETTINGS = config.get("default", "default_settings", fallback = Settings.DEFAULT_SETTINGS).replace('"', '')
	Settings.USE_DEFAULT_SETTINGS_ON_WRONG_PARAM = config.getboolean("default", "use_default_on_wrong_parameter", fallback = Settings.USE_DEFAULT_SETTINGS_ON_WRONG_PARAM)
	Settings.LOG_MESSAGE_TO_FILE = config.getboolean("default", "log_message_to_file", fallback = Settings.LOG_MESSAGE_TO_FILE)
	Settings.MESSAGE_LOG_FILE = config.get("default", "message_log_file", fallback = Settings.MESSAGE_LOG_FILE).replace('"', '')
	Settings.DATE_TIMEZONE = config.get("default", "date_timezone", fallback = Settings.DATE_TIMEZONE).replace('"', '')
	Settings.DATE_FORMAT = config.get("default", "date_format", fallback = Settings.DATE_FORMAT).replace('"', '')
	Settings.UNPACK_MULTI_TIFF = config.getboolean("default", "unpack_multipage_tiffs", fallback = Settings.UNPACK_MULTI_TIFF)

	# Prepare global logger after loading user settings (and logger address too)
	prepareGlobalLogger()

	# Chosen fax section
	# Check if settings section for chosen fax exists (or set it to default)
	if (whichFax == "") or (not config.has_section(whichFax)):
		if whichFax == "":
			logNotice(StringTable.NO_PARAMETER_SET)
		else:
			logNotice(StringTable.NO_SECTION + whichFax)

		if Settings.USE_DEFAULT_SETTINGS_ON_WRONG_PARAM:
			whichFax = Settings.DEFAULT_SETTINGS
			logNotice(StringTable.USING_DEFAULT + whichFax)
		else:
			logNotice(StringTable.NOT_USING_DEFAULT)

	# Get phone number and subject trigger for chosen fax
	Settings.PHONE_NUMBER = config.get(whichFax, "phone_number", fallback = Settings.PHONE_NUMBER).replace('"', '')
	Settings.SUBJECT_TRIGGER = config.get(whichFax, "subject_trigger", fallback = Settings.SUBJECT_TRIGGER).replace('"', '')

	# Get timezone for chosen fax
	if config.has_option(whichFax, "date_timezone"):
		Settings.DATE_TIMEZONE = config.get(whichFax, "date_timezone", fallback = Settings.DATE_TIMEZONE).replace('"', '')
		logNotice(StringTable.USING_TIMEZONE + Settings.DATE_TIMEZONE)

	# Get date format for chosen fax
	if config.has_option(whichFax, "date_format"):
		Settings.DATE_FORMAT = config.get(whichFax, "date_format", fallback = Settings.DATE_FORMAT).replace('"', '')
		logNotice(StringTable.USING_DATE_FORMAT + Settings.DATE_FORMAT)

	# Get setting for turning on/off logging a message to the file for chosen fax
	if config.has_option(whichFax, "log_message_to_file"):
		Settings.LOG_MESSAGE_TO_FILE = config.getboolean(whichFax, "log_message_to_file", fallback = Settings.LOG_MESSAGE_TO_FILE)
		logNotice("Logging message to a file setting overriden for " + whichFax + ": " + str(Settings.LOG_MESSAGE_TO_FILE))

	# Get file name for logging a message to for chosen fax
	if config.has_option(whichFax, "message_log_file"):
		Settings.MESSAGE_LOG_FILE = config.get(whichFax, "message_log_file", fallback = Settings.MESSAGE_LOG_FILE).replace('"', '')
		logNotice("Message log file setting overriden for " + whichFax + ": " + Settings.MESSAGE_LOG_FILE)

	# Replace loaded phone number if route is set
	if config.has_option(whichFax, "route_to"):
		Settings.ROUTE_TO_FAX = config.get(whichFax, "route_to", fallback = Settings.ROUTE_TO_FAX).replace('"', '')
		if Settings.ROUTE_TO_FAX == whichFax:
			logWarning(StringTable.ROUTE_SAME_1 + Settings.ROUTE_TO_FAX + StringTable.ROUTE_SAME_2)

		elif config.has_section(Settings.ROUTE_TO_FAX):
			try:
				Settings.PHONE_NUMBER = config.get(Settings.ROUTE_TO_FAX, "phone_number")
				logNotice(StringTable.USING_ROUTE + whichFax + StringTable.ROUTE_FROM_TO + Settings.ROUTE_TO_FAX)
				if config.has_option(Settings.ROUTE_TO_FAX, "route_to"):
					logWarning(StringTable.ROUTE_TO_NO_FOLLOW_1 + Settings.ROUTE_TO_FAX + StringTable.ROUTE_TO_NO_FOLLOW_2 + Settings.PHONE_NUMBER)
			except:
				logNotice(StringTable.ROUTE_NO_SETTINGS_1 + Settings.ROUTE_TO_FAX + StringTable.ROUTE_NO_SETTINGS_2 + whichFax + StringTable.ROUTE_NO_SETTINGS_3)

		else:
			logNotice(StringTable.ROUTE_NO_SETTINGS_1 + Settings.ROUTE_TO_FAX + StringTable.ROUTE_NO_SETTINGS_2 + whichFax + StringTable.ROUTE_NO_SETTINGS_3)

	Settings.SETTINGS_RELOADED = True

	return

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
		converter = HTMLFilter()
		converter.feed(findAmpChar(string))
		string = string.replace(findAmpChar(string), converter.text)
		position = string.find("&", position + 1)

		if position < 0:
			break

	return string

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
def mailDateToFormat(inp, timezone = "", format = "%Y-%m-%d %H:%M:%S"):
	try:
		return dateutil.parser.parse(inp).astimezone(dateutil.tz.gettz(timezone)).strftime(format)
	except:
		return inp

# Try..Except version of decodeHeader() function with returning None on empty strings
def tryDecodeHeader(header):
	try:
		return decodeHeader(header)
	except:
		return None

# Function for gathering main headers from message ("From", "Subject" and "Date")
def getMailInfo(message):
	s_from = tryDecodeHeader(message["From"])
	if s_from == None:
		s_from = Settings.NO_DATA

	s_subj = tryDecodeHeader(message["Subject"])
	if s_subj == None:
		s_subj = Settings.NO_DATA
	elif (s_subj[0:len(Settings.SUBJECT_TRIGGER)] == Settings.SUBJECT_TRIGGER) and (len(s_subj) > len(Settings.SUBJECT_TRIGGER)):
		if Settings.DELETE_SUBJECT_TRIGGER:
			s_subj = s_subj[len(Settings.SUBJECT_TRIGGER):]

	s_date = mailDateToFormat(tryDecodeHeader(message["Date"]), Settings.DATE_TIMEZONE, Settings.DATE_FORMAT)
	if s_date == None:
		s_date = Settings.NO_DATA

	return s_from, s_subj, s_date

# Function for preparing header to save as a text file
def prepareTextHeader(s_from, s_subj, s_date, addReturns = True):
	textHeader = Settings.SENDER + s_from + "\n"
	textHeader += Settings.SUBJECT + s_subj + "\n"
	textHeader += Settings.DATE + s_date

	if addReturns:
		textHeader += "\n\n"

	return textHeader

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

# Very simple get image format (if possible) utility
def quickImageFormat(data):
	try:
		return PIL.Image.open(io.BytesIO(data)).format.lower()
	except:
		return ""

# Very quick and simple "if-we-have-an-image" test
def quickImageTest(data):
	return quickImageFormat(data) != ""

# One function to save data to make code more readable
def saveMessagePart(binary, outFile, data, counter, s_subj, s_from):
	# Check if mode is correct according to the data
	if binary:
		# Change mode to non-binary if data is string
		if isinstance(data, str):
			binary = False
			outFile = str(counter) + ".txt"
			logNotice(StringTable.SAVE_IMAGE_1 + s_subj + StringTable.SAVE_IMAGE_2 + s_from + StringTable.SAVE_IMAGE_3)

	else:
		# Change mode to binary if data is binary
		if isinstance(data, bytes):
			binary = True

			if quickImageFormat(data) == "":
				# Let's say JPG is a default extension in such situation (should be harmless)
				outFile = str(counter) + ".jpg"
			else:
				outFile = str(counter) + "." + quickImageFormat(data)

			logNotice(StringTable.SAVE_TEXT_1 + s_subj + StringTable.SAVE_TEXT_2 + s_from + StringTable.SAVE_TEXT_3)

	if binary:
		fl = open(outFile, "wb")
	else:
		fl = open(outFile, "w")

	fl.write(data)
	fl.close()

	return outFile

# Wrapper for converting text to G3 TIFF image
def convertTextToTIFF(fileName, fileNameWithoutExt):
	tiffTools.textFileToTIFF(fileNameWithoutExt + ".tiff", fileName, 1, Settings.TEXT_FONT_NAME + " " + str(Settings.TEXT_FONT_SIZE), Settings.TEXT_TOP_MARGIN)
	return

# Wrapper for converting images to non-G3 TIFF files
def convertImageToTIFF(fileName, fileNameWithoutExt, pageWidth = 1728, marginLeft = 32, marginRight = 32):
	tiffTools.imageToTIFF(fileName, fileNameWithoutExt + ".tiff", pageWidth, marginLeft, marginRight)
	return

# Procedure for logging message contents to file
def logMessageToFile(filename, data):
	try:
		gLogFile = gzip.open(filename, "at")
		gLogFile.write(data)
		gLogFile.write("\n")
		gLogFile.close()

	except Exception as e:
		logError(StringTable.LOGGING_MESSAGE_FAILED)

	return

# Function for gathering image count in one file
def getImageCount(filename):
	img = PIL.Image.open(filename)
	imgCount = img.n_frames
	img.close()

	return imgCount

# Function for unpacking multipage TIFF files and place in the main temporary directory
def unpackTIFFandPrepare(counter, filename):
	newFileList = []

	try:
		# Prepare another temporary directory and change directory to it
		oldDir = os.getcwd()
		dir = tempfile.TemporaryDirectory()
		os.chdir(dir.name)

		# Split TIFF image
		tiffSplitCommand = ["tiffsplit", oldDir + "/" + filename]
		subprocess.run(tiffSplitCommand)

		# Get and sort single TIFF files
		fileList = os.listdir(".")
		fileList.sort()

		# Rename files according to the counter and move to the main temporary directory
		for file in fileList:
			os.rename(file, oldDir + "/" + str(counter) + ".tiff")
			newFileList += [str(counter) + ".tiff"]
			counter += 1

	finally:
		# Change back directory and clean up temporary directory
		os.chdir(oldDir)
		dir.cleanup()

	# Return list of additional files
	return newFileList

# Main program procedure for gathering mail data and process it
def getAndProcess(passBuffer = None, whichFax = ""):
	oldDir = os.getcwd()
	dir = tempfile.TemporaryDirectory()
	os.chdir(dir.name)
	outFile = ""
	buffer = ""
	counter = 1	# let's start from 1 at this point
	fileList = []
	first = True
	anything = False
	wasTextInMessage = False
	nothingUseful = False
	messageTriggered = False
	standardTriggered = False
	everythingOK = True

	# Prepare global logger if needed
	prepareGlobalLogger()

	if whichFax != "":
		if len(sys.argv) > 1:
			whichFax = sys.argv[1]
		else:
			whichFax = ""

	if not Settings.SETTINGS_RELOADED:
		loadSettings(whichFax = whichFax)

	# Stop further processing - there are not any phone number specified for faxing!
	if (Settings.PHONE_NUMBER == "") or (Settings.PHONE_NUMBER == None):
		logError(StringTable.NO_PHONE_NUMBER)
		return False

	try:
		# According to the situation (if parameter passed or not)
		if passBuffer == None:
			# Read the message from stdin
			for line in sys.stdin:
				buffer += line
		else:
			# Read the message from provided data
			buffer = passBuffer

		# Log message to the GZIP file
		if Settings.LOG_MESSAGE_TO_FILE:
			logMessageToFile(Settings.MESSAGE_LOG_FILE, buffer)

		# Import message and get main information from headers
		message = email.message_from_string(buffer)
		s_from, s_subj, s_date = getMailInfo(message)

		if message.is_multipart():
			parts = message.get_payload()
		else:
			parts = [message]

		# First plain or non-plain decision
		decidePlainOrHTML(parts)

		for part in parts:
			# Unpack text from multipart (plain and html decision)
			if part.is_multipart():
				# Second plain or non-plain decision
				parts2 = part.get_payload()
				decidePlainOrHTML(parts2)

				# Should not be more parts on the list at this point (so get the only one)
				part = parts2[0]

			# Decode all interesting information from headers at this point
			encoding = part.get_content_charset()

			# UTF-8 is default (if encoding not specified)
			if encoding == None:
				encoding = "utf-8"

			# Decode non plain-text data (Base64 or Quoted-Printable)
			if part["Content-Transfer-Encoding"] == "base64":
				data = base64.b64decode(part.get_payload())
			elif part["Content-Transfer-Encoding"] == "quoted-printable":
				data = email.quoprimime.body_decode(part.get_payload()).encode("latin1").decode(encoding)
			else:
				data = part.get_payload()

			# Get file name properties (to extract extension) and also try to
			# decode a filename (big thanks to MarX, who accidentally found that part missing!)
			filename = decodeHeader(part.get_filename())
			if filename == None:
				fN = ""
				fExt = ""
			else:
				fN, fExt = os.path.splitext(filename)

			# If there is nothing interesting in here, go to the next part
			if len(data) == 0:
				continue

			# Determine and store attachment's type information in temporary variables to make further code look better
			contentMimeType = determineMimeType(data)
			contentMainType = getMainType(contentMimeType)
			contentSubType = getSubType(contentMimeType)
			contentExtension = mimetypes.guess_extension(contentMimeType)

			# Change extension to this from mail if guessing failed
			if contentExtension == "":
				contentExtension = fExt

			# If guessed mime type doesn't match with what is in the mail
			if contentMimeType != part.get_content_type():
				# Additional condition, as otherwise html to text may not happen
				if contentMimeType == "text/plain" and part.get_content_type() == "text/html":
					contentMimeType = part.get_content_type()
					contentMainType = part.get_content_maintype()
					contentSubType = part.get_content_subtype()
					# File extension doesn't matter
				else:
					# Otherwise, log mime type override
					logNotice(StringTable.MIMETYPE_OVERRIDE_1 + s_subj + StringTable.MIMETYPE_OVERRIDE_2 + s_from + StringTable.MIMETYPE_OVERRIDE_3 + contentMimeType + StringTable.MIMETYPE_OVERRIDE_4 + part.get_content_type() + StringTable.MIMETYPE_OVERRIDE_5)

			# Additional (old) tests
			# Let's check if text/plain isn't in fact an image...
			if (contentMainType == "text") and isinstance(data, bytes) and quickImageTest(data):
				contentMainType = "image"
				logNotice(StringTable.SAVE_TEXT_1 + s_subj + StringTable.SAVE_TEXT_2 + s_from + StringTable.SAVE_TEXT_3)

			# Let's check if image/* isn't in fact a text...
			if (contentMainType == "image") and isinstance(data, str) and not quickImageTest(data):
				contentMainType = "text"
				logNotice(StringTable.SAVE_IMAGE_1 + s_subj + StringTable.SAVE_IMAGE_2 + s_from + StringTable.SAVE_IMAGE_3)

			if contentMainType == "text":
				# This will avoid discarding text attachments...
				messageTriggered = False

				# Get rid of "bytes" type if needed
				try:
					data = str(data, encoding)
				except:
					data = str(data)

				if contentSubType == "html":
					# Replace any <br> and <br /> to the new lines, because this simple HTMLFilter can't do this automatically
					data = data.replace("<br>", "\n").replace("<br />", "\n")
					converter = HTMLFilter()
					converter.feed(data)
					# This will simply convert HTML to the plain-text
					data = converter.text
				else:
					# Multispaces to new lines option
					if Settings.MSPACES_TONL:
						data = multiSpacesToReturns(data)
					# Changing amp characters option
					if Settings.AMPS_CHANGE:
						data = changeAmpChars(data)

				# Convert any CR+LF to just LF (big thanks to MariuszK, who accidentally found that part missing!)
				data = data.replace("\r\n", "\n")

				# Things to be done/checked once (in the first text part of the message)
				if first:
					# Add header to the text part (if possible)
					if len(data) == 0:
						data = prepareTextHeader(s_from, s_subj, s_date, False)
					else:
						data = prepareTextHeader(s_from, s_subj, s_date) + data

					# Are we going to use message triggers?
					if Settings.DELETE_MESSAGE_TRIGGER:
						# Is message triggered?
						messageTriggered = (data.find(Settings.MESSAGE_TRIGGER) != -1)

					# Are we going to use standard resolution trigger?
					if Settings.USE_STANDARD_TRIGGER:
						# Is message meant to be sent in the standard resolution?
						standardTriggered = (data.find(Settings.STANDARD_TRIGGER) != -1)

					# Is standard trigger has to be removed (only in first text part)?
					if Settings.DELETE_STANDARD_TRIGGER:
						# Delete it
						data=data.replace(Settings.STANDARD_TRIGGER, "")

					# "First-text-part-time" checks done; flag it
					first = False

				# Having those two conditions here below will probably make checks above a little slower
				# (in situations with e-mails containing huge amount of new lines at the beginning or
				# at the end), but will avoid situations, where there are huge amount of lines
				# with "!STANDARD!" trigger that will be changed to the empty lines and then not stripped

				# Remove leading and trailing new lines option
				if Settings.STRIP_BE_NLS:
					data = data.lstrip('\n').rstrip('\n')

				# Remove in-text more-than-two new lines option
				if Settings.STRIP_INTEXT_NLS:
					data = removeDuplicatedNewLines(data)

				# Save text to temporary file
				if not messageTriggered:
					outFile = str(counter) + ".txt"

					try:
						outFile = saveMessagePart(False, outFile, data, counter, s_subj, s_from)
					except:
						outFile = ""
						logNotice(StringTable.SAVE_TEXT_ERROR_1 + s_subj + StringTable.SAVE_TEXT_ERROR_2 + s_from + StringTable.SAVE_TEXT_ERROR_3)

				else:
					outFile = ""
					logNotice(StringTable.TEXT_DISCARDED_1 + s_subj + StringTable.TEXT_DISCARDED_2 + s_from + StringTable.TEXT_DISCARDED_3)

				wasTextInMessage = True

			elif contentMainType == "image":
				if(contentExtension != ""):
					# Additional test if attachment has correct extension (for too quick locally sent messages with image attachments)
					if contentExtension.lower() == ".txt":
						if quickImageFormat(data) == "":
							# Let's say JPG is a default extension if it is unknown
							contentExtension = ".jpg"
						else:
							contentExtension = "." + quickImageFormat(data)

					outFile = str(counter) + contentExtension

				elif(quickImageFormat(data) != ""):
					# Try to guess image format
					contentExtension = "." + quickImageFormat(data)
					# Update filename (again, big thanks to MarX, who accidentally found that part missing!)
					outFile = str(counter) + contentExtension

				else:
					# Try default image extension (using simply .jpg should be harmless)
					contentExtension = ".jpg"
					outFile = str(counter) + contentExtension

				try:
					# Very simple workaround for TIFF attachments (to leave space for converting files to .tiff without overwriting)
					if contentExtension.lower() == ".tiff":
						contentExtension = ".tif"
						outFile = str(counter) + contentExtension

					# Save it too
					outFile = saveMessagePart(True, outFile, data, counter, s_subj, s_from)

					# It's not a typo - extension here will be TIF (not TIFF!)
					if (Settings.UNPACK_MULTI_TIFF) and (contentExtension.lower() == ".tif"):
						imageCount = getImageCount(outFile)
						if imageCount > 1:
							fileList += unpackTIFFandPrepare(counter, outFile)
							counter += imageCount - 1
							outFile = ""

				except:
					outFile = ""
					logNotice(StringTable.SAVE_IMAGE_ERROR_1 + s_subj + StringTable.SAVE_IMAGE_ERROR_2 + s_from + StringTable.SAVE_IMAGE_ERROR_3)

			else:
				# If part of a message is not a text nor an image, then discard it (as it may be vulnerable)
				outFile = ""
				logNotice(StringTable.ATTACHMENT_DISCARDED_1 + s_subj + StringTable.ATTACHMENT_DISCARDED_2 + s_from + StringTable.ATTACHMENT_DISCARDED_3 + " (" + contentMimeType + ")")

			# Increase the file counter and add file to the list (if there is any)
			counter += 1
			if outFile != "":
				fileList += [outFile]

		# If message had no text part, then just add only a header
		if not wasTextInMessage:
			try:
				# The most ugly condition in this code (sorry to all for that)...
				if (fileList == []) and (s_from == Settings.NO_DATA) and (s_subj == Settings.NO_DATA) and (s_date == Settings.NO_DATA):
					logNotice(StringTable.NOTHING_TO_FAX)
					nothingUseful = True
				else:
					# Write '0.txt' file containing just headers and add it at the very beginning of the file list
					outFile = saveMessagePart(False, "0.txt", prepareTextHeader(s_from, s_subj, s_date, False), 0, s_subj, s_from)
					fileList = [outFile] + fileList

			except:
				logNotice(StringTable.HEADER_SAVE_ERROR_1 + s_subj + StringTable.HEADER_SAVE_ERROR_2 + s_from + StringTable.HEADER_SAVE_ERROR_3)

		# Now convert all the saved files (text and images) to the TIFFs
		for fileNumber in range(len(fileList)):
			# Unpack file name and extension
			fN, fExt = os.path.splitext(fileList[fileNumber])

			# Text files
			if fExt == ".txt":
				# Convert text files to G3 TIFFs
				convertTextToTIFF(fileList[fileNumber], fN)

				# Update the file name on the list
				fileList[fileNumber] = fN + ".tiff"

				# And apply the cutter (to prevent wasting paper on a fax machine)
				cutter.loadAndCrop(fileList[fileNumber])

			# Image files
			else:
				try:
					# Try to convert an image (if possible)
					convertImageToTIFF(fileList[fileNumber], fN)

					# Update the file name on the list
					fileList[fileNumber] = fN + ".tiff"

				except:
					# Probably corrupted image
					logNotice(StringTable.IMAGE_CORRUPTED_ERROR_1 + s_subj + StringTable.IMAGE_CORRUPTED_ERROR_2 + s_from + StringTable.IMAGE_CORRUPTED_ERROR_3)

		# Now prepare the faxspool command
		if standardTriggered:
			command = ["faxspool", "-n", Settings.PHONE_NUMBER]
		else:
			command = ["faxspool", Settings.PHONE_NUMBER]

		for file in fileList:
			# Add only TIFFs to the command (additional safety condition)
			if ".tiff" in file:
				if not anything:
					anything=True
				command += [file]

		# Run faxspool command only if there are anything to fax
		if anything:
			if standardTriggered:
				logNotice(StringTable.STANDARD_RESOLUTION_1 + s_subj + StringTable.STANDARD_RESOLUTION_2 + s_from + StringTable.STANDARD_RESOLUTION_3)

			subprocess.check_output(command)

		else:
			if not nothingUseful:
				logNotice(StringTable.NOTHING_TO_FAX_I_1 + s_subj + StringTable.NOTHING_TO_FAX_I_2 + s_from + StringTable.NOTHING_TO_FAX_I_3)

	except Exception as e:
		logError(str(e))
		everythingOK = False

	finally:
		os.chdir(oldDir)
		dir.cleanup()

	return everythingOK


# Autorun part
if __name__ == "__main__":
	# Set default exit code (0)
	exitCode = 0

	# Try to get and process incomming message
	try:
		if len(sys.argv) > 1:
			whichFax = sys.argv[1]
		else:
			whichFax = ""

		loadSettings(whichFax = whichFax)

		if getAndProcess():
			exitCode = 0
		else:
			exitCode = 1

	# I think it's much better this way
	except Exception as e:
		logError(str(e))
		exitCode = 1

	# And finally return exit code to the system
	os._exit(exitCode)
