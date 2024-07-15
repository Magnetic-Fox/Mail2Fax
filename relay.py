#!/usr/bin/env python3

# Simple E-Mail to Fax Utility
#
# by Magnetic-Fox, 15-16.07.2024
#
# (C)2024 Bartłomiej "Magnetic-Fox" Węgrzyn!

import tempfile
import email
import email.header
import sys
import os
import subprocess
import base64

# Simple string table
NO_DATA=	"(brak danych)"
SENDER=		"Nadawca: "
SUBJECT=	"Temat:   "
DATE=		"Data:    "

# Fax number
PHONE_NUMBER=	"1001"

# Mail header decoding helper
def decodeHeader(input):
	output=""
	if input!=None:
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
	oldDir=os.getcwd()
	dir=tempfile.TemporaryDirectory()
	os.chdir(dir.name)
	buffer=""
	counter=1
	fileList=[]
	first=True
	anything=False
	try:
		for line in sys.stdin:
			buffer+=line

		message=email.message_from_string(buffer)

		if message.is_multipart():
			parts=message.get_payload()
		else:
			parts=[message]

		for part in parts:
			if part["Content-Transfer-Encoding"]=="base64":
				data=base64.b64decode(part.get_payload())
			else:
				data=part.get_payload()
			filename=part.get_filename()
			if filename==None:
				fN=""
				fExt=""
			else:
				fN, fExt = os.path.splitext(filename)
			if len(data)==0:
				continue
			if part.get_content_maintype()=="text":
				if first:
					data=str(data)
					s_from=decodeHeader(message["From"])
					if s_from==None:
						s_from=NO_DATA
					s_subj=decodeHeader(message["Subject"])
					if s_subj==None:
						s_subj=NO_DATA
					s_date=decodeHeader(message["Date"])
					if s_date==None:
						s_date=NO_DATA
					firstData =SENDER+s_from+"\n"
					firstData+=SUBJECT+s_subj+"\n"
					firstData+=DATE+s_date+"\n\n"
					data=firstData+data
					first=False
				outFile=str(counter)+".txt"
				fl=open(outFile,"w")
				fl.write(data)
				fl.close()
			elif part.get_content_maintype()=="image":
				if(fExt!=""):
					outFile=str(counter)+fExt
				else:
					outFile=str(counter)+".jpg"
				fl=open(outFile,"wb")
				fl.write(data)
				fl.close()
			else:
				outFile=""

			counter+=1
			if outFile!="":
				fileList+=[outFile]

		for x in range(len(fileList)):
			fN, fExt = os.path.splitext(fileList[x])
			if fExt==".txt":
				paps=subprocess.Popen(["paps","--top-margin=6",fileList[x]], stdout=subprocess.PIPE)
				subprocess.check_output(["gs","-sDEVICE=tiffg3","-sOutputFile="+fN+".tiff","-dBATCH","-dNOPAUSE","-dSAFER","-dQUIET","-"], stdin=paps.stdout)
				paps.wait()
				fileList[x]=fN+".tiff"
			else:
				subprocess.check_output(["convert",fileList[x],fN+".tiff"])
				fileList[x]=fN+".tiff"

		command=["faxspool",str(PHONE_NUMBER)]

		for file in fileList:
			if ".tiff" in file:
				if not anything:
					anything=True
				command+=[file]

		if anything:
			subprocess.check_output(command)

	finally:
		os.chdir(oldDir)
		dir.cleanup()

	return

# Autorun
if __name__ == "__main__":
	main()
	exit(0)
