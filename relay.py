#!/usr/bin/env python3

################################################################################
#
# Simple E-Mail to Fax Relay Utility for Procmail
#
# by Magnetic-Fox, 13.07.2024 - 05.04.2025
#
# (C)2024-2025 Bartłomiej "Magnetic-Fox" Węgrzyn!
#
################################################################################

# Imports...
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

################################################################################

# Main constants
# Logger texts constants
LOGGER_ERROR=		"relay.py: error: "
LOGGER_NOTICE=		"relay.py: notice: "

# Default settings constants
SETTINGS_NO_DATA=	"(no data)"
SETTINGS_SENDER=	"Sender:  "
SETTINGS_SUBJECT=	"Subject: "
SETTINGS_DATE=		"Date:    "
SETTINGS_PHONE_NUMBER=	""
SETTINGS_DEL_SUB_TRIG=	True
SETTINGS_DEL_MESS_TRIG=	True
SETTINGS_SUBJECT_TRIG=	"[FAX] "
SETTINGS_MESSAGE_TRIG=	"!DISCARD!"
SETTINGS_USE_PLAIN=	True

# String table
# Image saving
STR_SAVE_IMAGE_1=	'Going to save image part of the message "'
STR_SAVE_IMAGE_2=	'" from "'
STR_SAVE_IMAGE_3=	'" as a text file (probably wrong content type in the message)'

# Text saving
STR_SAVE_TEXT_1=	'Going to save text part of the message "'
# same value as STR_SAVE_IMAGE_2
STR_SAVE_TEXT_2=	STR_SAVE_IMAGE_2
STR_SAVE_TEXT_3=	'" as an image file (probably wrong content type in the message)'

# No phone number
STR_NO_PHONE_NUMBER=	"No phone number specified!"

# Saving text error
STR_SAVE_TEXT_ERROR_1=	'Saving text from message "'
# same value as STR_SAVE_IMAGE_2
STR_SAVE_TEXT_ERROR_2=	STR_SAVE_IMAGE_2
STR_SAVE_TEXT_ERROR_3=	'" was not possible'

# Saving image error
STR_SAVE_IMAGE_ERROR_1=	'Saving image from message "'
# same value as STR_SAVE_IMAGE_2 and STR_SAVE_TEXT_ERROR_3
STR_SAVE_IMAGE_ERROR_2=	STR_SAVE_IMAGE_2
STR_SAVE_IMAGE_ERROR_3=	STR_SAVE_TEXT_ERROR_3

# Attachment discarded
STR_ATTACHMENT_DISC_1=	'Discarded an attachment from message "'
# same value as STR_SAVE_IMAGE_2
STR_ATTACHMENT_DISC_2=	STR_SAVE_IMAGE_2
STR_ATTACHMENT_DISC_3=	'"'

# Nothing to fax error
STR_NOTHING_TO_FAX=	"There was nothing to fax from the message"

# Saving headers error
STR_HEAD_SAVE_ERROR_1=	'Saving headers from message "'
# same value as STR_SAVE_IMAGE_2 and STR_SAVE_TEXT_ERROR_3
STR_HEAD_SAVE_ERROR_2=	STR_SAVE_IMAGE_2
STR_HEAD_SAVE_ERROR_3=	STR_SAVE_TEXT_ERROR_3

# Corrupted image error
STR_IMAGE_CORR_ERR_1=	'Skipped corrupted image file from the message titled "'
# same value as STR_SAVE_IMAGE_2 and STR_ATTACHMENT_DISC_3
STR_IMAGE_CORR_ERR_2=	STR_SAVE_IMAGE_2
STR_IMAGE_CORR_ERR_3=	STR_ATTACHMENT_DISC_3

# More informative "nothing to fax" error
STR_NOTHING_TO_FAX_I_1=	'There was nothing to fax from message titled "'
# same value as STR_SAVE_IMAGE_2 and STR_ATTACHMENT_DISC_3
STR_NOTHING_TO_FAX_I_2=	STR_SAVE_IMAGE_2
STR_NOTHING_TO_FAX_I_3=	STR_ATTACHMENT_DISC_3

################################################################################

# Main global variable
settingsLoaded=False

################################################################################

# Functions...
# Simple procedure for passing error messages to the system log
def logError(errorString):
	subprocess.check_output(["logger",LOGGER_ERROR+errorString])
	return

# Simple procedure for passing notices to the system log
def logNotice(noticeString):
        subprocess.check_output(["logger",LOGGER_NOTICE+noticeString])
        return

# Procedure for loading settings from the INI file
def loadSettings(settingsFile="relay_settings.ini"):
	global NO_DATA, SENDER, SUBJECT, DATE, PHONE_NUMBER, DELETE_SUBJECT_TRIGGER, DELETE_MESSAGE_TRIGGER, SUBJECT_TRIGGER, MESSAGE_TRIGGER, USE_PLAIN, settingsLoaded

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
	NO_DATA=config.get("strings","no_data",fallback=SETTINGS_NO_DATA).replace('"','')
	SENDER=config.get("strings","sender",fallback=SETTINGS_SENDER).replace('"','')
	SUBJECT=config.get("strings","subject",fallback=SETTINGS_SUBJECT).replace('"','')
	DATE=config.get("strings","date",fallback=SETTINGS_DATE).replace('"','')
	PHONE_NUMBER=config.get("phone","number",fallback=SETTINGS_PHONE_NUMBER).replace('"','')
	DELETE_SUBJECT_TRIGGER=config.getboolean("message","delete_subject_trigger",fallback=SETTINGS_DEL_SUB_TRIG)
	DELETE_MESSAGE_TRIGGER=config.getboolean("message","delete_message_trigger",fallback=SETTINGS_DEL_MESS_TRIG)
	SUBJECT_TRIGGER=config.get("message","subject_trigger",fallback=SETTINGS_SUBJECT_TRIG).replace('"','')
	MESSAGE_TRIGGER=config.get("message","message_trigger",fallback=SETTINGS_MESSAGE_TRIG).replace('"','')
	USE_PLAIN=config.getboolean("message","use_plain",fallback=SETTINGS_USE_PLAIN)

	# Note that everything has finished
	settingsLoaded=True

	return

# Great HTML to text part found on Stack Overflow
class HTMLFilter(html.parser.HTMLParser):
	text=""
	def handle_data(self, data):
		self.text+=data

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

# Try..Except version of decodeHeader() function with returning NO_DATA on empty strings
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
		s_from=NO_DATA

	# Get mail subject
	s_subj=tryDecodeHeader(message["Subject"])
	if s_subj==None:
		s_subj=NO_DATA
	elif (s_subj[0:len(SUBJECT_TRIGGER)]==SUBJECT_TRIGGER) and (len(s_subj)>len(SUBJECT_TRIGGER)):
		if DELETE_SUBJECT_TRIGGER:
			s_subj=s_subj[len(SUBJECT_TRIGGER):]

	# Get mail date
	s_date=mailDateToFormat(tryDecodeHeader(message["Date"]))
	if s_date==None:
		s_date=NO_DATA

	# Return information
	return s_from, s_subj, s_date

# Function for preparing header for the text file
def prepareTextHeader(s_from, s_subj, s_date, addReturns=True):
	textHeader =SENDER+s_from+"\n"
	textHeader+=SUBJECT+s_subj+"\n"
	textHeader+=DATE+s_date

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
	if USE_PLAIN:
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
			logNotice(STR_SAVE_IMAGE_1+s_subj+STR_SAVE_IMAGE_2+s_from+STR_SAVE_IMAGE_3)
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
			logNotice(STR_SAVE_TEXT_1+s_subj+STR_SAVE_TEXT_2+s_from+STR_SAVE_TEXT_3)

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
def getAndProcess(passBuffer=None):
	# Prepare everything
	everythingOK=True

	# Load settings if needed
	if not settingsLoaded:
		loadSettings()

	# Stop further processing - there are not any phone number to fax specified!
	if (PHONE_NUMBER=="") or (PHONE_NUMBER==None):
		logError(STR_NO_PHONE_NUMBER)
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
			filename=part.get_filename()
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

			# For example, test if text/plain isn't in fact an image...
			if (type(data)==bytes) and (quickImageTest(data)):
				contentMainType="image"

			# If we're dealing with text part
			if contentMainType=="text":
				# Get rid of "bytes" type (which is a bit annoying thing in Python)
				try:
					data=str(data,encoding)
				except:
					data=str(data)

				# Convert HTML to text
				if part.get_content_subtype()=="html":
					# Replace any <br> and <br /> to the new lines (well, this simple HTMLFilter can't do this)
					data=data.replace("<br>","\n").replace("<br />","\n")
					converter=HTMLFilter()
					converter.feed(data)
					data=converter.text

				# Convert any CR+LF to just LF (big thanks to MariuszK, who accidentally found that part missing!)
				data=data.replace("\r\n","\n")

				# Remove any leading and trailing returns (helps not to waste fax machine's recording paper)
				data=data.lstrip('\n').rstrip('\n')

				# And this is out first time
				if first:
					# Then add some information from the header (if possible)
					if len(data)==0:
						data=prepareTextHeader(s_from,s_subj,s_date,False)
					else:
						data=prepareTextHeader(s_from,s_subj,s_date)+data
					first=False

				# Is message triggered?
				messageTriggered=MESSAGE_TRIGGER in data
				if not DELETE_MESSAGE_TRIGGER:
					messageTriggered=False

				# Save text to temporary file
				if not messageTriggered:
					outFile=str(counter)+".txt"
					try:
						outFile=saveMessagePart(False, outFile, data, counter, s_subj, s_from)
					except:
						outFile=""
						logNotice(STR_SAVE_TEXT_ERROR_1+s_subj+STR_SAVE_TEXT_ERROR_2+s_from+STR_SAVE_TEXT_ERROR_3)

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
					fExt="."+quickImageFormat(data)
				else:
					# Default...
					outFile=str(counter)+".jpg"
				try:
					# Save it too
					outFile=saveMessagePart(True, outFile, data, counter, s_subj, s_from)
				except:
					outFile=""
					logNotice(STR_SAVE_IMAGE_ERROR_1+s_subj+STR_SAVE_IMAGE_ERROR_2+s_from+STR_SAVE_IMAGE_ERROR_3)

			# Or something else?
			else:
				# Discard it (as it may be vulnerable)
				outFile=""
				logNotice(STR_ATTACHMENT_DISC_1+s_subj+STR_ATTACHMENT_DISC_2+s_from+STR_ATTACHMENT_DISC_3)

			# Increase the file counter and add file to the list (if there is any)
			counter+=1
			if outFile!="":
				fileList+=[outFile]

		# If message had no text part, then add just the header
		if not wasTextInMessage:
			try:
				# Yeah, a little ugly condition (comparing strings instead of making own, more sophisticated class for variables...)
				# However, testing if there are any files in the list and if we got any usable information at this point
				if (fileList==[]) and (s_from==NO_DATA) and (s_subj==NO_DATA) and (s_date==NO_DATA):
					logNotice(STR_NOTHING_TO_FAX)
					nothingUseful=True
				else:
					# Write '0.txt' file containing just headers and add it at the very beginning of the file list
					outFile=saveMessagePart(False, "0.txt", prepareTextHeader(s_from,s_subj,s_date,False), 0, s_subj, s_from)
					fileList=[outFile]+fileList
			except:
				logNotice(STR_HEAD_SAVE_ERROR_1+s_subj+STR_HEAD_SAVE_ERROR_2+s_from+STR_HEAD_SAVE_ERROR_3)

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
					logNotice(STR_IMAGE_CORR_ERR_1+s_subj+STR_IMAGE_CORR_ERR_2+s_from+STR_IMAGE_CORR_ERR_3)

		# Now prepare the faxspool command
		command=["faxspool",PHONE_NUMBER]

		for file in fileList:
			# Add only the TIFFs (additional safety condition)
			if ".tiff" in file:
				if not anything:
					anything=True
				command+=[file]

		# If we got anything that can be sent
		if anything:
			# Then send it
			subprocess.check_output(command)
		else:
			# If not, let's log it
			if not nothingUseful:
				logNotice(STR_NOTHING_TO_FAX_I_1+s_subj+STR_NOTHING_TO_FAX_I_2+s_from+STR_NOTHING_TO_FAX_I_3)

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

################################################################################

# Autorun part
if __name__ == "__main__":
	# Try to get and process incomming message
	try:
		loadSettings()
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
