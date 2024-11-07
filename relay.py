#!/usr/bin/env python3

# Simple E-Mail to Fax Relay Utility for Procmail
#
# by Magnetic-Fox, 13.07.2024 - 07.11.2024
#
# (C)2024 Bartłomiej "Magnetic-Fox" Węgrzyn!

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

# Main global variable
SETTINGS_LOADED=False

# Simple procedure for passing error messages to the system log
def logError(errorString):
	subprocess.check_output(["logger","relay.py: error: "+errorString])
	return

# Simple procedure for passing notices to the system log
def logNotice(noticeString):
        subprocess.check_output(["logger","relay.py: notice: "+noticeString])
        return

# Procedure for loading settings from the INI file
def loadSettings(settingsFile="relay_settings.ini"):
	global NO_DATA, SENDER, SUBJECT, DATE, PHONE_NUMBER, DELETE_SUBJECT_TRIGGER, DELETE_MESSAGE_TRIGGER, SUBJECT_TRIGGER, MESSAGE_TRIGGER, USE_PLAIN, SETTINGS_LOADED

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
	NO_DATA=config.get("strings","no_data",fallback="(no data)").replace('"','')
	SENDER=config.get("strings","sender",fallback="Sender:  ").replace('"','')
	SUBJECT=config.get("strings","subject",fallback="Subject: ").replace('"','')
	DATE=config.get("strings","date",fallback="Date:    ").replace('"','')
	PHONE_NUMBER=config.get("phone","number",fallback="").replace('"','')
	DELETE_SUBJECT_TRIGGER=config.getboolean("message","delete_subject_trigger",fallback=True)
	DELETE_MESSAGE_TRIGGER=config.getboolean("message","delete_message_trigger",fallback=True)
	SUBJECT_TRIGGER=config.get("message","subject_trigger",fallback="[FAX] ").replace('"','')
	MESSAGE_TRIGGER=config.get("message","message_trigger",fallback="!DISCARD!").replace('"','')
	USE_PLAIN=config.getboolean("message","use_plain",fallback=True)

	# Note that everything has finished
	SETTINGS_LOADED=True

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
	if output=="":
		return None
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

# Main program procedure
def getAndProcess(passBuffer=None):
	# Prepare everything
	everythingOK=True

	# Load settings if needed
	if not SETTINGS_LOADED:
		loadSettings()

	# Stop further processing - there are not any phone number to fax specified!
	if (PHONE_NUMBER=="") or (PHONE_NUMBER==None):
		logError("No phone number specified!")
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

		# Additional variables
		plainInt=[]
		nonPlInt=[]
		index=0

		# Additional testing
		for test in parts:
			if "text" in test.get_content_type():
				if "plain" in test.get_content_type():
					plainInt+=[index]
				else:
					nonPlInt+=[index]
			index+=1

		# Remove only if other parts exists (plain and html decision)
		if USE_PLAIN:
			if plainInt!=[]:
				for i in reversed(nonPlInt):
					parts.pop(i)
		else:
			if nonPlInt!=[]:
				for i in reversed(plainInt):
					parts.pop(i)

		# Now process all parts of the message
		for part in parts:
			# Unpack text from multipart (plain and html decision)
			if part.is_multipart():
				# Plain temporary variable
				pl=None

				# Non-plain temporary variable
				ot=None

				# Get all info
				for micropart in part.get_payload():
					if micropart.get_content_subtype()=="plain":
						pl=micropart
					else:
						ot=micropart

				# Decide
				if USE_PLAIN:
					if pl==None:
						if ot!=None:
							part=ot
					else:
						part=pl
				else:
					if ot==None:
						if pl!=None:
							part=pl
					else:
						part=ot

			# Decode all interesting information from headers at this point
			encoding=part.get_content_charset()
			if encoding==None:
				encoding="utf-8"

			if part["Content-Transfer-Encoding"]=="base64":
				data=base64.b64decode(part.get_payload())
			elif part["Content-Transfer-Encoding"]=="quoted-printable":
				data=email.quoprimime.body_decode(part.get_payload()).encode("latin1").decode(encoding)
			else:
				data=part.get_payload()

			filename=part.get_filename()
			if filename==None:
				fN=""
				fExt=""
			else:
				fN,fExt=os.path.splitext(filename)

			# If there is nothing interesting in here, go to the next part
			if len(data)==0:
				continue

			# If we're dealing with text part
			if part.get_content_maintype()=="text":
				# Get rid of "bytes" type (which is a bit annoying thing in Python)
				try:
					data=str(data,encoding)
				except:
					data=str(data)

				# Convert HTML to text
				if part.get_content_subtype()=="html":
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
						fl=open(outFile,"w")
						fl.write(data)
						fl.close()
					except:
						outFile=""
						logNotice('Saving text from message "'+s_subj+'" from "'+s_from+'" was not possible')

				# Set information that message had text part
				wasTextInMessage=True

			# Or maybe we got an image?
			elif part.get_content_maintype()=="image":
				if(fExt!=""):
					outFile=str(counter)+fExt
				else:
					# Let's say JPG is a default extension if it is unknown
					outFile=str(counter)+".jpg"
				try:
					# Save it too
					if type(data)==str:
						# But if the data type claims it's a text, save it as a text file (maybe we've got a message with wrong content-type?)
						outFile=str(counter)+".txt"
						fl=open(outFile,"w")
						fl.write(data)
						fl.close()
						logNotice('Saved image part of the message "'+s_subj+'" from "'+s_from+'" as a text file (probably wrong content type in the message)')
					else:
						# Save data if that's really data
						fl=open(outFile,"wb")
						fl.write(data)
						fl.close()
				except:
					outFile=""
					logNotice('Saving image from message "'+s_subj+'" from "'+s_from+'" was not possible')

			# Or something else?
			else:
				# Discard it (as it may be vulnerable)
				outFile=""
				logNotice('Discarded an attachment from message "'+s_subj+'" from "'+s_from+'"')

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
					logNotice("There was nothing to fax from the message")
					nothingUseful=True
				else:
					# Write '0.txt' file containing just headers
					fl=open("0.txt","w")
					fl.write(prepareTextHeader(s_from,s_subj,s_date,False))
					fl.close()
					# And add it on the very beginning of the file list
					fileList=["0.txt"]+fileList
			except:
				logNotice('Saving headers from message "'+s_subj+'" from "'+s_from+'" was not possible')

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
					logNotice('Skipped corrupted image file from the message titled "'+s_subj+'" from "'+s_from+'"')

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
				logNotice('There was nothing to fax from message titled "'+s_subj+'" from "'+s_from+'"')

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
