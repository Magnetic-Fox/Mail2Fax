#!/usr/bin/env python3

# String table for E-Mail to Fax Relay Utility for Procmail and MGetty-Fax (faxspool)
#
# by Magnetic-Fox, 16.10.2025 - 03.11.2025
#
# (C)2025 Bartłomiej "Magnetic-Fox" Węgrzyn!

LOGGER_RELAY_NAME = "FAX-Relay"
LOGGER_ERROR = LOGGER_RELAY_NAME + ": error: "
LOGGER_WARNING = LOGGER_RELAY_NAME + ": warning: "
LOGGER_NOTICE = LOGGER_RELAY_NAME + ": notice: "
SAVE_IMAGE_1 = 'Going to save image part of the message "'
SAVE_IMAGE_2 = '" from "'
SAVE_IMAGE_3 = '" as a text file (probably wrong content type in the message)'
SAVE_TEXT_1 = 'Going to save text part of the message "'
SAVE_TEXT_2 = SAVE_IMAGE_2
SAVE_TEXT_3 = '" as an image file (probably wrong content type in the message)'
MIMETYPE_OVERRIDE_1 = 'Overriding mime type for attachment in message "'
MIMETYPE_OVERRIDE_2 = '" from "'
MIMETYPE_OVERRIDE_3 = '" to: '
MIMETYPE_OVERRIDE_4 = " (previous: "
MIMETYPE_OVERRIDE_5 = ")"
NO_PHONE_NUMBER = "No phone number specified!"
SAVE_TEXT_ERROR_1 = 'Saving text from message "'
SAVE_TEXT_ERROR_2 = SAVE_IMAGE_2
SAVE_TEXT_ERROR_3 = '" was not possible'
SAVE_IMAGE_ERROR_1 = 'Saving image from message "'
SAVE_IMAGE_ERROR_2 = SAVE_IMAGE_2
SAVE_IMAGE_ERROR_3 = SAVE_TEXT_ERROR_3
ATTACHMENT_DISCARDED_1 = 'Discarded an attachment from message "'
ATTACHMENT_DISCARDED_2 = SAVE_IMAGE_2
ATTACHMENT_DISCARDED_3 = '"'
NOTHING_TO_FAX = "There was nothing to fax from the message"
HEADER_SAVE_ERROR_1 = 'Saving headers from message "'
HEADER_SAVE_ERROR_2 = SAVE_IMAGE_2
HEADER_SAVE_ERROR_3 = SAVE_TEXT_ERROR_3
IMAGE_CORRUPTED_ERROR_1 = 'Skipped corrupted image file from the message titled "'
IMAGE_CORRUPTED_ERROR_2 = SAVE_IMAGE_2
IMAGE_CORRUPTED_ERROR_3 = ATTACHMENT_DISCARDED_3
NOTHING_TO_FAX_I_1 = 'There was nothing to fax from message titled "'
NOTHING_TO_FAX_I_2 = SAVE_IMAGE_2
NOTHING_TO_FAX_I_3 = ATTACHMENT_DISCARDED_3
NO_SECTION = 'No settings for: '
NO_PARAMETER_SET = 'No setting parameter!'
USING_DEFAULT = 'Using default, which is: '
NOT_USING_DEFAULT = 'Not using default!'
TEXT_DISCARDED_1 = 'Text part of the message "'
TEXT_DISCARDED_2 = SAVE_IMAGE_2
TEXT_DISCARDED_3 = '" discarded due to the message trigger'
STANDARD_RESOLUTION_1 = 'Standard resolution triggered for message "'
STANDARD_RESOLUTION_2 = SAVE_IMAGE_2
STANDARD_RESOLUTION_3 = ATTACHMENT_DISCARDED_3
ROUTE_SAME_1 = "Route "
ROUTE_SAME_2 = " points to the same settings, ignoring"
USING_ROUTE = "Using route "
ROUTE_FROM_TO = " -> "
ROUTE_TO_NO_FOLLOW_1 = "Settings for "
ROUTE_TO_NO_FOLLOW_2 = " has defined route_to option, which won't be followed. Will use phone number: "
ROUTE_NO_SETTINGS_1 = "Route set, but no settings for "
ROUTE_NO_SETTINGS_2 = ", using previous settings ("
ROUTE_NO_SETTINGS_3 = ")"
USING_TIMEZONE = "Using timezone: "
USING_DATE_FORMAT = "Using date format: "
LOGGING_MESSAGE_FAILED = "Logging message to file failed!"
