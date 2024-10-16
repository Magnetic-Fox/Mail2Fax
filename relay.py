#!/usr/bin/env python3

# Simple E-Mail to Fax Relay Utility for Procmail
#
# by Magnetic-Fox, 13-24.07.2024, 19-25.08.2024, 16.10.2024
#
# (C)2024 Bartłomiej "Magnetic-Fox" Węgrzyn!

import tempfile
import email
import email.header
import email.quoprimime
import sys
import os
import subprocess
import base64
import html.parser
import consts_relay
import dateutil
import datetime
import cutter
import PIL.Image

SETTINGS_LOADED=False

def loadSettings(noData=None, sender=None, subject=None, date=None, phoneNumber=None, deleteSubjectTrigger=None, deleteMessageTrigger=None, subjectTrigger=None, messageTrigger=None, usePlain=None):
	global NO_DATA, SENDER, SUBJECT, DATE, PHONE_NUMBER, DELETE_SUBJECT_TRIGGER, DELETE_MESSAGE_TRIGGER, SUBJECT_TRIGGER, MESSAGE_TRIGGER, USE_PLAIN, SETTINGS_LOADED

	# load defaults or change something (if possible)

	# Simple string table
	if noData==None:
		NO_DATA=	"(no data)"
	elif noData!="":
		NO_DATA=	noData
	if sender==None:
		SENDER=		"Sender:  "
	elif sender!="":
		SENDER=		sender
	if subject==None:
		SUBJECT=	"Subject: "
	elif subject!="":
		SUBJECT=	subject
	if date==None:
		DATE=		"Date:    "
	elif date!="":
		DATE=		date

	# Fax number (the default is my internal fax number - You may change it here, or pass yours to the function)
	if phoneNumber==None:
		PHONE_NUMBER=	"1001"
	elif phoneNumber!="":
		PHONE_NUMBER=	phoneNumber

	# Triggers control
	if deleteSubjectTrigger==None:
		DELETE_SUBJECT_TRIGGER=True
	elif deleteSubjectTrigger!="":	# a bit stupid, but why not?
		DELETE_SUBJECT_TRIGGER=deleteSubjectTrigger
	if deleteMessageTrigger==None:
		DELETE_MESSAGE_TRIGGER=True
	elif deleteMessageTrigger!="":	# ditto
		DELETE_MESSAGE_TRIGGER=deleteMessageTrigger

	# Subject trigger to be removed
	if subjectTrigger==None:
		SUBJECT_TRIGGER="[FAX] "
	elif subjectTrigger!="":
		SUBJECT_TRIGGER=subjectTrigger

	# Message trigger (string that make text part rejected at the output)
	if messageTrigger==None:
		MESSAGE_TRIGGER="?????NOTEXT?????"
	elif messageTrigger!="":
		MESSAGE_TRIGGER=messageTrigger

	# What text version use when it comes to decide - plain or html?
	if usePlain==None:
		USE_PLAIN=True
	elif usePlain!="":	# ditto
		USE_PLAIN=usePlain

	# Are settings loaded?
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
		# try to decode header info
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
	return output

# Simple utility to make date/time more readable if possible
def mailDateToFormat(inp, format="%Y-%m-%d %H:%M:%S"):
	try:
		localTimeZone=datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset()
		temp=dateutil.parser.parse(inp)
		offset=temp.utcoffset()
		temp=temp.replace(tzinfo=None)
		if offset==None:
			if localTimeZone!=None:
				temp+=localTimeZone
		else:
			if localTimeZone==None:
				temp-=offset
			else:
				temp+=(localTimeZone-offset)
		return temp.strftime(format)
	except:
		return inp

# Main program procedure
def getAndProcess():
	# prepare everything
	if not SETTINGS_LOADED:
		loadSettings()
	oldDir=os.getcwd()
	dir=tempfile.TemporaryDirectory()
	os.chdir(dir.name)
	outFile=""
	buffer=""
	counter=1
	fileList=[]
	first=True
	anything=False
	try:
		# read the message from stdin
		for line in sys.stdin:
			buffer+=line

		# import it
		message=email.message_from_string(buffer)

		# and preprocess
		if message.is_multipart():
			parts=message.get_payload()
		else:
			parts=[message]

		# now process all parts of the message
		for part in parts:
			# Unpack text from multipart (plain and html decision)
			if part.is_multipart():
				# Plain temporary variable
				pl=None

				# Non-plain temporary variable
				ot=None
				for micropart in part.get_payload():
					if micropart.get_content_subtype()=="plain":
						pl=micropart
					else:
						ot=micropart
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

			# decode all interesting information from headers at this point
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
				fN, fExt = os.path.splitext(filename)

			# if there is nothing interesting in here, go to the next part
			if len(data)==0:
				continue

			# if we're dealing with text part
			if part.get_content_maintype()=="text":
				# get rid of "bytes" type (which is a bit annoying thing in Python)
				try:
					data=str(data,encoding)
				except:
					data=str(data)

				# convert HTML to text
				if part.get_content_subtype()=="html":
					converter=HTMLFilter()
					converter.feed(data)
					data=converter.text

				# convert any CR+LF to just LF (big thanks to MariuszK, who found that part missing!)
				data=data.replace("\r\n","\n")

				# and this is out first time
				if first:
					# then add some information from the header (if possible)
					s_from=decodeHeader(message["From"])
					if s_from==None:
						s_from=NO_DATA
					s_subj=decodeHeader(message["Subject"])
					if s_subj==None:
						s_subj=NO_DATA
					elif (s_subj[0:len(SUBJECT_TRIGGER)]==SUBJECT_TRIGGER) and (len(s_subj)>len(SUBJECT_TRIGGER)):
						if DELETE_SUBJECT_TRIGGER:
							# well, i think subject trigger part isn't really necessary here ;)
							s_subj=s_subj[len(SUBJECT_TRIGGER):]
					s_date=mailDateToFormat(decodeHeader(message["Date"]))
					if s_date==None:
						s_date=NO_DATA
					firstData =SENDER+s_from+"\n"
					firstData+=SUBJECT+s_subj+"\n"
					firstData+=DATE+s_date+"\n\n"
					data=firstData+data
					first=False

				# is message triggered?
				messageTriggered=MESSAGE_TRIGGER in data
				if not DELETE_MESSAGE_TRIGGER:
					messageTriggered=False

				# save text to temporary file
				if not messageTriggered:
					outFile=str(counter)+".txt"
					fl=open(outFile,"w")
					fl.write(data)
					fl.close()

			# or maybe we got an image?
			elif part.get_content_maintype()=="image":
				if(fExt!=""):
					outFile=str(counter)+fExt
				else:
					outFile=str(counter)+".jpg"
				try:
					# save it too
					fl=open(outFile,"wb")
					fl.write(data)
					fl.close()
				except:
					# or just ignore if mail has wrong content-type info
					pass

			# or something else?
			else:
				outFile=""
				# discard it (it may be vulnerable)

			counter+=1
			if outFile!="":
				fileList+=[outFile]

		# now, process all the saved files
		for x in range(len(fileList)):
			fN, fExt = os.path.splitext(fileList[x])
			if fExt==".txt":
				# convert text files to G3 TIFFs
				paps=subprocess.Popen(["paps","--top-margin=6","--font=Monospace 10",fileList[x]], stdout=subprocess.PIPE)
				subprocess.check_output(["gs","-sDEVICE=tiffg3","-sOutputFile="+fN+".tiff","-dBATCH","-dNOPAUSE","-dSAFER","-dQUIET","-"], stdin=paps.stdout)
				paps.wait()

				# update the file name on the list
				fileList[x]=fN+".tiff"

				# and apply the cutter (to waste less paper on a fax machine)
				cutter.loadAndCrop(fileList[x])
			else:
				# temporary variable
				rotate=False

				# test if image is landscape or portrait
				img=PIL.Image.open(fileList[x])
				width,height=img.size
				img.close()
				rotate=width>height

				# prepare command
				command=["convert",fileList[x]]

				# rotate image if necessary
				if rotate:
					command+=["-rotate","90"]

				command+=["-resize","1664>","-background","white","-gravity","northwest","-splice","32x0","-background","white","-gravity","northeast","-splice","32x0",fN+".tiff"]

				# convert images to TIFFs with auto-size and auto-margin
				subprocess.check_output(command)

				# update the file name on the list
				fileList[x]=fN+".tiff"

		# now prepare the faxspool command
		command=["faxspool",str(PHONE_NUMBER)]

		for file in fileList:
			# add only the TIFFs (additional safety condition)
			if ".tiff" in file:
				if not anything:
					anything=True
				command+=[file]

		# if we got anything that can be sent
		if anything:
			# then send it
			subprocess.check_output(command)
			pass

	finally:
		# finish everything
		os.chdir(oldDir)
		dir.cleanup()

	# we're done ;)
	return

# Autorun part
if __name__ == "__main__":
	# Try to get and process incomming message
	try:
		consts_relay.setConsts(loadSettings)
		getAndProcess()

	# I think it's much better this way
	except Exception as e:
		subprocess.check_output(["logger","relay.py: error: "+str(e)])
		exit(1)

	# And finally return 0 exit code
	finally:
		exit(0)
