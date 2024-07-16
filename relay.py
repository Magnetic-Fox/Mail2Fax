#!/usr/bin/env python3

# Simple E-Mail to Fax Relay Utility for Procmail
#
# by Magnetic-Fox, 13-16.07.2024
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

# Simple string table (in Polish, but hope it's self-explanatory ;))
NO_DATA=	"(brak danych)"
SENDER=		"Nadawca: "
SUBJECT=	"Temat:   "
DATE=		"Data:    "

# Fax number (my internal phone number - You may change it)
PHONE_NUMBER=	"1001"

# Subject trigger to be removed (leave the space)
SUBJECT_TRIGGER="[FAX] "

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

# Main program code
def main():
	# prepare everything
	oldDir=os.getcwd()
	dir=tempfile.TemporaryDirectory()
	os.chdir(dir.name)
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
						# well, i think subject trigger part isn't really necessary here ;)
						s_subj=s_subj[len(SUBJECT_TRIGGER):]
					s_date=decodeHeader(message["Date"])
					if s_date==None:
						s_date=NO_DATA
					firstData =SENDER+s_from+"\n"
					firstData+=SUBJECT+s_subj+"\n"
					firstData+=DATE+s_date+"\n\n"
					data=firstData+data
					first=False
				# save text to temporary file
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
				# save it too
				fl=open(outFile,"wb")
				fl.write(data)
				fl.close()

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
				paps=subprocess.Popen(["paps","--top-margin=6",fileList[x]], stdout=subprocess.PIPE)
				subprocess.check_output(["gs","-sDEVICE=tiffg3","-sOutputFile="+fN+".tiff","-dBATCH","-dNOPAUSE","-dSAFER","-dQUIET","-"], stdin=paps.stdout)
				paps.wait()
				# and update the file name on the list
				fileList[x]=fN+".tiff"
			else:
				# convert images to TIFFs
				subprocess.check_output(["convert",fileList[x],fN+".tiff"])
				# and update the file name on the list
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

	finally:
		# finish everything
		os.chdir(oldDir)
		dir.cleanup()

	# we're done ;)
	return

# Autorun part
if __name__ == "__main__":
	try:
		main()
	except:
		exit(1)
	exit(0)
