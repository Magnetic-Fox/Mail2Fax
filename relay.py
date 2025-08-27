#!/usr/bin/env python3

# E-Mail to Fax Relay Utility for Procmail and MGetty-Fax (faxspool)
#
# Utilizing PAPS, GhostScript, ImageMagick (convert), Pillow (PIL)
# and system logger (logger)
#
# Software intended for use on Linux systems (especially Debian)
# because of calling conventions and specific system utilities used
#
# by Magnetic-Fox, 13.07.2024 - 27.08.2025
#
# (C)2024-2025 Bartłomiej "Magnetic-Fox" Węgrzyn!

import tempfile
import email
import email.header
import email.quoprimime
import sys
import os
import subprocess
import base64
import html.parser
import dateutil
import datetime
import cutter
import PIL.Image
import configparser
import io

# Settings class (with default settings applied)
class Settings:
	SETTINGS_FILE=				"relay_settings.ini"
	SETTINGS_RELOADED=			False
	NO_DATA=				"(no data)"
	SENDER=					"Sender:  "
	SUBJECT=				"Subject: "
	DATE=					"Date:    "
	PHONE_NUMBER=				""
	DELETE_SUBJECT_TRIGGER=			True
	DELETE_MESSAGE_TRIGGER=			True
	SUBJECT_TRIGGER=			"[FAX] "
	MESSAGE_TRIGGER=			"!DISCARD!"
	STANDARD_TRIGGER=			"!STANDARD!"
	USE_STANDARD_TRIGGER=			True
	DELETE_STANDARD_TRIGGER=		True
	USE_PLAIN=				True
	MSPACES_TONL=				False
	AMPS_CHANGE=				False
	DEFAULT_SETTINGS=			"FAX"
	USE_DEFAULT_SETTINGS_ON_WRONG_PARAM=	False
	STRIP_BE_NLS=				True
	STRIP_INTEXT_NLS=			True

# String table class
class StringTable:
	LOGGER_ERROR=				"relay.py: error: "
	LOGGER_NOTICE=				"relay.py: notice: "
	SAVE_IMAGE_1=				'Going to save image part of the message "'
	SAVE_IMAGE_2=				'" from "'
	SAVE_IMAGE_3=				'" as a text file (probably wrong content type in the message)'
	SAVE_TEXT_1=				'Going to save text part of the message "'
	SAVE_TEXT_2=				SAVE_IMAGE_2
	SAVE_TEXT_3=				'" as an image file (probably wrong content type in the message)'
	NO_PHONE_NUMBER=			"No phone number specified!"
	SAVE_TEXT_ERROR_1=			'Saving text from message "'
	SAVE_TEXT_ERROR_2=			SAVE_IMAGE_2
	SAVE_TEXT_ERROR_3=			'" was not possible'
	SAVE_IMAGE_ERROR_1=			'Saving image from message "'
	SAVE_IMAGE_ERROR_2=			SAVE_IMAGE_2
	SAVE_IMAGE_ERROR_3=			SAVE_TEXT_ERROR_3
	ATTACHMENT_DISCARDED_1=			'Discarded an attachment from message "'
	ATTACHMENT_DISCARDED_2=			SAVE_IMAGE_2
	ATTACHMENT_DISCARDED_3=			'"'
	NOTHING_TO_FAX=				"There was nothing to fax from the message"
	HEADER_SAVE_ERROR_1=			'Saving headers from message "'
	HEADER_SAVE_ERROR_2=			SAVE_IMAGE_2
	HEADER_SAVE_ERROR_3=			SAVE_TEXT_ERROR_3
	IMAGE_CORRUPTED_ERROR_1=		'Skipped corrupted image file from the message titled "'
	IMAGE_CORRUPTED_ERROR_2=		SAVE_IMAGE_2
	IMAGE_CORRUPTED_ERROR_3=		ATTACHMENT_DISCARDED_3
	NOTHING_TO_FAX_I_1=			'There was nothing to fax from message titled "'
	NOTHING_TO_FAX_I_2=			SAVE_IMAGE_2
	NOTHING_TO_FAX_I_3=			ATTACHMENT_DISCARDED_3
	NO_SECTION=				'No settings for: '
	NO_PARAMETER_SET=			'No setting parameter!'
	USING_DEFAULT=				'Using default, which is: '
	NOT_USING_DEFAULT=			'Not using default!'
	TEXT_DISCARDED_1=			'Text part of the message "'
	TEXT_DISCARDED_2=			SAVE_IMAGE_2
	TEXT_DISCARDED_3=			'" discarded due to the message trigger'
	STANDARD_RESOLUTION_1=			'Standard resolution triggered for message "'
	STANDARD_RESOLUTION_2=			SAVE_IMAGE_2
	STANDARD_RESOLUTION_3=			ATTACHMENT_DISCARDED_3

# Simple new line characters counter
def countNewLines(data,position):
	count=0
	while data.find("\n",position)==position:
		count=count+1
		position=position+1
	return count

# Simple duplicated new line characters remover
def removeDuplicatedNewLines(data):
	while data.find("\n\n\n")!=-1:
		count=countNewLines(data,data.find("\n\n\n"))
		data=data.replace("\n"*count,"\n\n")
	return data

# Simple spaces counter
def spacesCount(string, position):
	for x in range(position,len(string)):
		if(string[x]!=' '):
			return x-position
	if(position<=len(string)):
		return len(string)-position
	else:
		return 0

# Multi spaces to returns
def multiSpacesToReturns(string):
	while(string.find("  ")!=-1):
		# Not really optimized line, but I didn't want to use regexes ;)
		string=string.replace(" "*spacesCount(string,string.find("  ")),"\n"*(spacesCount(string,string.find("  "))-1),1)
	return string

# Simple procedure for passing error messages to the system log
def logError(errorString):
	subprocess.check_output(["logger",StringTable.LOGGER_ERROR+errorString])
	return

# Simple procedure for passing notices to the system log
def logNotice(noticeString):
        subprocess.check_output(["logger",StringTable.LOGGER_NOTICE+noticeString])
        return

# Procedure for loading settings from the INI file
def loadSettings(whichFax="", settingsFile=Settings.SETTINGS_FILE):
	# Create parser object and try to load the settings file
	config=configparser.ConfigParser()
	if config.read(settingsFile)==[]:
		# Try finding file in the script's path
		try:
			settingsFile=os.path.dirname(os.path.realpath(__file__))+"/"+settingsFile
			config.read(settingsFile)
		except:
			pass

	# Load settings if possible (or defaults, if not)
	Settings.NO_DATA=				config.get("strings","no_data",					fallback=Settings.NO_DATA).replace('"','')
	Settings.SENDER=				config.get("strings","sender",					fallback=Settings.SENDER).replace('"','')
	Settings.SUBJECT=				config.get("strings","subject",					fallback=Settings.SUBJECT).replace('"','')
	Settings.DATE=					config.get("strings","date",					fallback=Settings.DATE).replace('"','')
	Settings.MESSAGE_TRIGGER=			config.get("message","message_trigger",				fallback=Settings.MESSAGE_TRIGGER).replace('"','')
	Settings.STANDARD_TRIGGER=			config.get("message","standard_trigger",			fallback=Settings.STANDARD_TRIGGER).replace('"','')
	Settings.DEFAULT_SETTINGS=			config.get("default","default_settings",			fallback=Settings.DEFAULT_SETTINGS).replace('"','')
	Settings.DELETE_SUBJECT_TRIGGER=		config.getboolean("message","delete_subject_trigger",		fallback=Settings.DELETE_SUBJECT_TRIGGER)
	Settings.DELETE_MESSAGE_TRIGGER=		config.getboolean("message","delete_message_trigger",		fallback=Settings.DELETE_MESSAGE_TRIGGER)
	Settings.DELETE_STANDARD_TRIGGER=		config.getboolean("message","delete_standard_trigger",		fallback=Settings.DELETE_STANDARD_TRIGGER)
	Settings.USE_STANDARD_TRIGGER=			config.getboolean("message","use_standard_trigger",		fallback=Settings.USE_STANDARD_TRIGGER)
	Settings.USE_PLAIN=				config.getboolean("message","use_plain",			fallback=Settings.USE_PLAIN)
	Settings.MSPACES_TONL=				config.getboolean("message","multispaces_to_new_lines",		fallback=Settings.MSPACES_TONL)
	Settings.AMPS_CHANGE=				config.getboolean("message","convert_amp_characters",		fallback=Settings.AMPS_CHANGE)
	Settings.USE_DEFAULT_SETTINGS_ON_WRONG_PARAM=	config.getboolean("default","use_default_on_wrong_parameter",	fallback=Settings.USE_DEFAULT_SETTINGS_ON_WRONG_PARAM)
	Settings.STRIP_BE_NLS=				config.getboolean("message","strip_new_lines_on_startend",	fallback=Settings.STRIP_BE_NLS)
	Settings.STRIP_INTEXT_NLS=			config.getboolean("message","strip_intext_new_lines",		fallback=Settings.STRIP_INTEXT_NLS)

	# Load settings for the chosen fax
	if (whichFax=="") or (not config.has_section(whichFax)):
		if whichFax=="":
			logNotice(StringTable.NO_PARAMETER_SET)
		else:
			logNotice(StringTable.NO_SECTION+whichFax)
		if Settings.USE_DEFAULT_SETTINGS_ON_WRONG_PARAM:
			whichFax=Settings.DEFAULT_SETTINGS
			logNotice(StringTable.USING_DEFAULT+whichFax)
		else:
			logNotice(StringTable.NOT_USING_DEFAULT)

	# Get phone number and the subject trigger
	Settings.PHONE_NUMBER=				config.get(whichFax,"phone_number",				fallback=Settings.PHONE_NUMBER).replace('"','')
	Settings.SUBJECT_TRIGGER=			config.get(whichFax,"subject_trigger",				fallback=Settings.SUBJECT_TRIGGER).replace('"','')

	# Note that everything has finished
	Settings.SETTINGS_RELOADED=True

	return

# Great HTML to text part found on Stack Overflow
class HTMLFilter(html.parser.HTMLParser):
	text=""
	def handle_data(self, data):
		self.text+=data

# Function for finding HTML-style amp character
def findAmpChar(string, position=0):
	ampPos=string.find('&',position)
	endPos=string.find(';',ampPos)
	if endPos>ampPos:
		return string[ampPos:endPos+1]
	else:
		return ""

# Function for changing all HTML-style amp characters
def changeAmpChars(string):
	position=0
	while(findAmpChar(string,position)!=""):
		converter=HTMLFilter()
		converter.feed(findAmpChar(string))
		string=string.replace(findAmpChar(string),converter.text)
		position=string.find("&",position+1)
		if position<0:
			break
	return string

# Mail header decoding helper
def decodeHeader(input):
	output=""
	if input!=None:
		# Try to decode header info
		parts=email.header.decode_header(input)
		for part in parts:
			if part[1]==None:
				encoding="ascii"
			else:
				encoding=part[1]
			try:
				output+=str(part[0],encoding)
			except:
				output+=part[0]

	# If output is nothing the set it to None
	if output=="":
		output=None

	# Return output
	return output

# Much simplier and better utility to make date/time more readable and to deal with timezones if possible (relatively to the local timezone)
def mailDateToFormat(inp, format="%Y-%m-%d %H:%M:%S"):
	try:
		return dateutil.parser.parse(inp).astimezone().strftime(format)
	except:
		return inp

# Try..Except version of decodeHeader() function with returning None on empty strings
def tryDecodeHeader(header):
	try:
		return decodeHeader(header)
	except:
		return None

# Function for gathering "From", "Subject" and "Date" headers from message
def getMailInfo(message):
	# Get mail sender
	s_from=tryDecodeHeader(message["From"])
	if s_from==None:
		s_from=Settings.NO_DATA

	# Get mail subject
	s_subj=tryDecodeHeader(message["Subject"])
	if s_subj==None:
		s_subj=Settings.NO_DATA
	elif (s_subj[0:len(Settings.SUBJECT_TRIGGER)]==Settings.SUBJECT_TRIGGER) and (len(s_subj)>len(Settings.SUBJECT_TRIGGER)):
		if Settings.DELETE_SUBJECT_TRIGGER:
			s_subj=s_subj[len(Settings.SUBJECT_TRIGGER):]

	# Get mail date
	s_date=mailDateToFormat(tryDecodeHeader(message["Date"]))
	if s_date==None:
		s_date=Settings.NO_DATA

	# Return information
	return s_from, s_subj, s_date

# Function for preparing header for the text file
def prepareTextHeader(s_from, s_subj, s_date, addReturns=True):
	textHeader =Settings.SENDER+s_from+"\n"
	textHeader+=Settings.SUBJECT+s_subj+"\n"
	textHeader+=Settings.DATE+s_date

	if addReturns:
		textHeader+="\n\n"

	return textHeader

# Procedure grouping plain-text and non-plain-text parts of the message (indexed output)
def groupTypesIndexes(parts, plainInt, nonPlInt):
	index=0
	for test in parts:
		if "text" in test.get_content_type():
			if "plain" in test.get_content_type():
				plainInt+=[index]
			else:
				nonPlInt+=[index]
		index+=1
	return

# Procedure removing indexes depending on "use plain text" setting
def plainAndHTMLDecision(parts, plainInt, nonPlInt):
	if Settings.USE_PLAIN:
		if plainInt!=[]:
			for i in reversed(nonPlInt):
				parts.pop(i)
	else:
		if nonPlInt!=[]:
			for i in reversed(plainInt):
				parts.pop(i)
	return

# Binding procedure for plain or non-plain decision
def decidePlainOrHTML(parts):
	plainInt=[]
	nonPlInt=[]
	groupTypesIndexes(parts,plainInt,nonPlInt)
	plainAndHTMLDecision(parts,plainInt,nonPlInt)
	return

# Very simple get image format (if possible) utility
def quickImageFormat(data):
	try:
		return PIL.Image.open(io.BytesIO(data)).format.lower()
	except:
		return ""

# Very quick and simple "if-we-have-an-image" test
def quickImageTest(data):
	return quickImageFormat(data)!=""

# One function to save data to make code more readable
def saveMessagePart(binary, outFile, data, counter, s_subj, s_from):
	# Check if mode is correct according to the data
	if binary:
		# Change mode to non-binary if data is string
		if type(data)==str:
			binary=False
			outFile=str(counter)+".txt"
			# Log this change
			logNotice(StringTable.SAVE_IMAGE_1+s_subj+StringTable.SAVE_IMAGE_2+s_from+StringTable.SAVE_IMAGE_3)
	else:
		# Change mode to binary if data is binary
		if type(data)==bytes:
			binary=True
			if quickImageFormat(data)=="":
				# Let's say JPG is a default extension in such situation (should be harmless)
				outFile=str(counter)+".jpg"
			else:
				outFile=str(counter)+"."+quickImageFormat(data)
			# Log this change
			logNotice(StringTable.SAVE_TEXT_1+s_subj+StringTable.SAVE_TEXT_2+s_from+StringTable.SAVE_TEXT_3)

	# Open file properly
	if binary:
		fl=open(outFile,"wb")
	else:
		fl=open(outFile,"w")

	# Write data and close file
	fl.write(data)
	fl.close()

	# Finish
	return outFile

# Main program procedure
def getAndProcess(passBuffer=None, whichFax=""):
	# Check and get parameter
	if whichFax!="":
		if len(sys.argv)>1:
			whichFax=sys.argv[1]
		else:
			whichFax=""

	# Prepare everything
	everythingOK=True

	# Load settings if needed
	if not Settings.SETTINGS_RELOADED:
		loadSettings(whichFax=whichFax)

	# Stop further processing - there are not any phone number to fax specified!
	if (Settings.PHONE_NUMBER=="") or (Settings.PHONE_NUMBER==None):
		logError(StringTable.NO_PHONE_NUMBER)
		everythingOK=False
		return everythingOK

	# Initialize...
	oldDir=os.getcwd()
	dir=tempfile.TemporaryDirectory()
	os.chdir(dir.name)
	outFile=""
	buffer=""
	counter=1
	fileList=[]
	first=True
	anything=False
	wasTextInMessage=False
	nothingUseful=False
	messageTriggered=False
	standardTriggered=False

	# And now let's do anything needed...
	try:
		# If function was executed without buffer parameter...
		if passBuffer==None:
			# Read the message from stdin
			for line in sys.stdin:
				buffer+=line
		else:
			# Read the message from provided data
			buffer=passBuffer

		# Import it
		message=email.message_from_string(buffer)

		# Get message information
		s_from,s_subj,s_date=getMailInfo(message)

		# And preprocess
		if message.is_multipart():
			parts=message.get_payload()
		else:
			parts=[message]

		# First plain or non-plain decision
		decidePlainOrHTML(parts)

		# Now process all parts of the message
		for part in parts:
			# Unpack text from multipart (plain and html decision)
			if part.is_multipart():
				# Second plain or non-plain decision
				parts2=part.get_payload()
				decidePlainOrHTML(parts2)

				# Should not be more parts on the list at this point, so simply...
				part=parts2[0]

			# Decode all interesting information from headers at this point
			encoding=part.get_content_charset()

			# UTF-8 will be default
			if encoding==None:
				encoding="utf-8"

			# Decode message (Base64 or Quoted-Printable)
			if part["Content-Transfer-Encoding"]=="base64":
				data=base64.b64decode(part.get_payload())
			elif part["Content-Transfer-Encoding"]=="quoted-printable":
				data=email.quoprimime.body_decode(part.get_payload()).encode("latin1").decode(encoding)
			else:
				data=part.get_payload()

			# Get file name properties (to extract extension)
			# Try also to decode filename (big thanks to MarX, who accidentally found that part missing!)
			filename=decodeHeader(part.get_filename())
			if filename==None:
				fN=""
				fExt=""
			else:
				fN,fExt=os.path.splitext(filename)

			# If there is nothing interesting in here, go to the next part
			if len(data)==0:
				continue

			# Let's store it in its own variable to make some other tests
			contentMainType=part.get_content_maintype()

			# Let's check if text/plain isn't in fact an image...
			if (contentMainType=="text") and (type(data)==bytes) and (quickImageTest(data)):
				contentMainType="image"
				# Log this change
				logNotice(StringTable.SAVE_TEXT_1+s_subj+StringTable.SAVE_TEXT_2+s_from+StringTable.SAVE_TEXT_3)

			# Let's check if image/* isn't in fact a text...
			if (contentMainType=="image") and (type(data)==str) and (not quickImageTest(data)):
				contentMainType="text"
				# Log this change
				logNotice(StringTable.SAVE_IMAGE_1+s_subj+StringTable.SAVE_IMAGE_2+s_from+StringTable.SAVE_IMAGE_3)

			# If we're dealing with text part
			if contentMainType=="text":
				# Get rid of "bytes" type (which is a bit annoying thing in Python)
				try:
					data=str(data,encoding)
				except:
					data=str(data)

				# If HTML then convert it to text
				if part.get_content_subtype()=="html":
					# Replace any <br> and <br /> to the new lines (well, this simple HTMLFilter can't do this)
					data=data.replace("<br>","\n").replace("<br />","\n")
					converter=HTMLFilter()
					converter.feed(data)
					data=converter.text
				# If not HTML
				else:
					# If multispaces to new lines option activated (which should be avoided)
					if Settings.MSPACES_TONL:
						# well, then convert them
						data=multiSpacesToReturns(data)
					# If changing amp characters option activated (which also should be avoided)
					if Settings.AMPS_CHANGE:
						# well, then convert them
						data=changeAmpChars(data)

				# Convert any CR+LF to just LF (big thanks to MariuszK, who accidentally found that part missing!)
				data=data.replace("\r\n","\n")

				# If set to...
				if Settings.STRIP_BE_NLS:
					# then remove any leading and trailing returns (helps not to waste fax machine's recording paper)
					data=data.lstrip('\n').rstrip('\n')

				# If set to...
				if Settings.STRIP_INTEXT_NLS:
					# then remove any in-text more-than-two returns (also helps not to waste fax machine's recording paper)
					data=removeDuplicatedNewLines(data)

				# And this is out first time
				if first:
					# Then add some information from the header (if possible)
					if len(data)==0:
						data=prepareTextHeader(s_from,s_subj,s_date,False)
					else:
						data=prepareTextHeader(s_from,s_subj,s_date)+data
					first=False

				# Is message triggered?
				messageTriggered=(data.find(Settings.MESSAGE_TRIGGER)!=-1)
				if not Settings.DELETE_MESSAGE_TRIGGER:
					messageTriggered=False

				# If we are going to use standard resolution trigger?
				if Settings.USE_STANDARD_TRIGGER:
					# Is fax going to be sent in standard resolution?
					standardTriggered=(data.find(Settings.STANDARD_TRIGGER)!=-1)
					if Settings.DELETE_STANDARD_TRIGGER:
						data=data.replace(Settings.STANDARD_TRIGGER,"")

				# Save text to temporary file
				if not messageTriggered:
					outFile=str(counter)+".txt"
					try:
						outFile=saveMessagePart(False, outFile, data, counter, s_subj, s_from)
					except:
						outFile=""
						logNotice(StringTable.SAVE_TEXT_ERROR_1+s_subj+StringTable.SAVE_TEXT_ERROR_2+s_from+StringTable.SAVE_TEXT_ERROR_3)
				else:
					logNotice(StringTable.TEXT_DISCARDED_1+s_subj+StringTable.TEXT_DISCARDED_2+s_from+StringTable.TEXT_DISCARDED_3)

				# Set information that message had text part
				wasTextInMessage=True

			# Or maybe we got an image?
			elif contentMainType=="image":
				if(fExt!=""):
					# Additional test if attachment has correct extension
					if fExt.lower()==".txt":
						if quickImageFormat(data)=="":
							# Let's say JPG is a default extension if it is unknown
							fExt=".jpg"
						else:
							fExt="."+quickImageFormat(data)
					outFile=str(counter)+fExt
				elif(quickImageFormat(data)!=""):
					# Try to guess image format
					fExt="."+quickImageFormat(data)
					# Update filename (again, big thanks to MarX, who accidentally found that part missing!)
					outFile=str(counter)+fExt
				else:
					# Default...
					outFile=str(counter)+".jpg"
				try:
					# Save it too
					outFile=saveMessagePart(True, outFile, data, counter, s_subj, s_from)
				except:
					outFile=""
					logNotice(StringTable.SAVE_IMAGE_ERROR_1+s_subj+StringTable.SAVE_IMAGE_ERROR_2+s_from+StringTable.SAVE_IMAGE_ERROR_3)

			# Or something else?
			else:
				# Discard it (as it may be vulnerable)
				outFile=""
				logNotice(StringTable.ATTACHMENT_DISCARDED_1+s_subj+StringTable.ATTACHMENT_DISCARDED_2+s_from+StringTable.ATTACHMENT_DISCARDED_3)

			# Increase the file counter and add file to the list (if there is any)
			counter+=1

			if outFile!="":
				fileList+=[outFile]

		# If message had no text part, then add just the header
		if not wasTextInMessage:
			try:
				# Yeah, a little ugly condition (comparing strings instead of making own, more sophisticated class for variables...)
				# However, testing if there are any files in the list and if we got any usable information at this point
				if (fileList==[]) and (s_from==Settings.NO_DATA) and (s_subj==Settings.NO_DATA) and (s_date==Settings.NO_DATA):
					logNotice(StringTable.NOTHING_TO_FAX)
					nothingUseful=True
				else:
					# Write '0.txt' file containing just headers and add it at the very beginning of the file list
					outFile=saveMessagePart(False, "0.txt", prepareTextHeader(s_from,s_subj,s_date,False), 0, s_subj, s_from)
					fileList=[outFile]+fileList
			except:
				logNotice(StringTable.HEADER_SAVE_ERROR_1+s_subj+StringTable.HEADER_SAVE_ERROR_2+s_from+StringTable.HEADER_SAVE_ERROR_3)

		# Now, process all the saved files
		for x in range(len(fileList)):
			fN,fExt=os.path.splitext(fileList[x])
			if fExt==".txt":
				# Convert text files to G3 TIFFs
				paps=subprocess.Popen(["paps","--top-margin=6","--font=Monospace 10",fileList[x]], stdout=subprocess.PIPE)
				subprocess.check_output(["gs","-sDEVICE=tiffg3","-sOutputFile="+fN+".tiff","-dBATCH","-dNOPAUSE","-dSAFER","-dQUIET","-"], stdin=paps.stdout)
				paps.wait()

				# Update the file name on the list
				fileList[x]=fN+".tiff"

				# And apply the cutter (to prevent wasting paper on a fax machine)
				cutter.loadAndCrop(fileList[x])
			else:
				# Try to convert an image (if possible)
				try:
					# Temporary variable
					rotate=False

					# Test if image is landscape or portrait
					img=PIL.Image.open(fileList[x])
					width,height=img.size
					img.close()
					rotate=width>height

					# Prepare command
					command=["convert",fileList[x]]

					# Rotate image if necessary
					if rotate:
						command+=["-rotate","90"]

					command+=["-resize","1664>","-background","white","-gravity","northwest","-splice","32x0","-background","white","-gravity","northeast","-splice","32x0",fN+".tiff"]

					# Convert images to TIFFs with auto-size and auto-margin
					subprocess.check_output(command)

					# Update the file name on the list
					fileList[x]=fN+".tiff"

				# If reading an image isn't possible, skip it, but leave a notice in log
				except:
					logNotice(StringTable.IMAGE_CORRUPTED_ERROR_1+s_subj+StringTable.IMAGE_CORRUPTED_ERROR_2+s_from+StringTable.IMAGE_CORRUPTED_ERROR_3)

		# Now prepare the faxspool command
		if standardTriggered:
			command=["faxspool","-n",Settings.PHONE_NUMBER]
		else:
			command=["faxspool",Settings.PHONE_NUMBER]

		for file in fileList:
			# Add only the TIFFs (additional safety condition)
			if ".tiff" in file:
				if not anything:
					anything=True
				command+=[file]

		# If we got anything that can be sent
		if anything:
			# If standard resolution triggered
			if standardTriggered:
				# Then log it
				logNotice(StringTable.STANDARD_RESOLUTION_1+s_subj+StringTable.STANDARD_RESOLUTION_2+s_from+StringTable.STANDARD_RESOLUTION_3)
			# Then send it
			subprocess.check_output(command)
		else:
			# If not, let's log it
			if not nothingUseful:
				logNotice(StringTable.NOTHING_TO_FAX_I_1+s_subj+StringTable.NOTHING_TO_FAX_I_2+s_from+StringTable.NOTHING_TO_FAX_I_3)

	# I think it's good to log any error (so bugs can be reported)
	except Exception as e:
		logError(str(e))
		everythingOK=False

	# Finish everything
	finally:
		os.chdir(oldDir)
		dir.cleanup()

	# We're done ;)
	return everythingOK

# Autorun part
if __name__ == "__main__":
	# Try to get and process incomming message
	try:
		if len(sys.argv)>1:
			whichFax=sys.argv[1]
		else:
			whichFax=""
		loadSettings(whichFax=whichFax)
		if getAndProcess():
			exit(0)
		else:
			exit(1)

	# I think it's much better this way
	except Exception as e:
		logError(str(e))
		exit(1)

	# And finally return 0 exit code
	finally:
		exit(0)
