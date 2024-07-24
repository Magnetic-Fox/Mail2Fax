#!/usr/bin/env python3

# Constant settings to set in main relay script
#
# by Magnetic-Fox, 24.07.2024
#
# (C)2024 Bartłomiej "Magnetic-Fox" Węgrzyn!

# Constants (in Polish)
noData=			"(brak danych)"
sender=			"Nadawca: "
subject=		"Temat:   "
date=			"Data:    "
phoneNumber=		"1001"
deleteSubjectTrigger=	True
deleteMessageTrigger=	True
subjectTrigger=		"[FAX] "
messageTrigger=		"?????NOTEXT?????"
usePlain=		True

# Simple function to load constants
def setConsts(loadSettingsFunc):
	loadSettingsFunc(noData,sender,subject,date,phoneNumber,deleteSubjectTrigger,deleteMessageTrigger,subjectTrigger,messageTrigger,usePlain)
	return
