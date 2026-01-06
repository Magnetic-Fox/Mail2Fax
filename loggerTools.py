#!/usr/bin/env python3

# Logger tools
#
# by Magnetic-Fox, 13.07.2024 - 06.01.2026
#
# (C)2024-2026 Bartłomiej "Magnetic-Fox" Węgrzyn!

import gzip
import logging
import logging.handlers


# Simple logger preparation function
def prepareLogger(loggerName = __name__, loggerAddress = "/dev/log"):
	logger = logging.getLogger(loggerName)
	handler = logging.handlers.SysLogHandler(address = loggerAddress)

	logger.setLevel(logging.INFO)
	logger.addHandler(handler)

	return logger

# Simple logging utility
def logInfo(logger, message, prefix = ""):
	logger.info(prefix + message)
	return

# Simple data to GZip logger
def logToCompressedFile(filename, data):
	gLogFile = gzip.open(filename, "at")
	gLogFile.write(data)
	gLogFile.write("\n")
	gLogFile.close()
	return
