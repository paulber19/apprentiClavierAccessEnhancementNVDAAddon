# appModules\apprenticlavier\ac_config.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright (C) 2019-2020, Paulber19
# This file is covered by the GNU General Public License.

# Manages ApprentiClavier add-on configuration.
import addonHandler
from logHandler import log
import os
from configobj import ConfigObj, ConfigObjError
import globalVars
import sys
addon = addonHandler.getCodeAddon()
path = os.path.join(addon.path, "shared")
sys.path.append(path)
from ac_py3Compatibility import importStringIO  # noqa:E402
del sys.path[-1]
StringIO = importStringIO()
# ConfigObj 5.1.0 and later integrates validate module.
try:
	from configobj.validate import Validator, VdtTypeError
except ImportError:
	from validate import Validator, VdtTypeError

# config section
SCT_General = "General"
SCT_Debit_General = "Debit General"
SCT_Debit_Explication = "Debit Explication"
SCT_Debit_Lesson_14 = "Debit lesson 14"
SCT_Debit_Lesson_15 = "Debit lesson 15"
SCT_Debit_Dictee_18 = "Debit dictee 18"
SCT_Debit_Dictee_19 = "Debit dictee 19"

# general section item
IT_MaxSpeed = "MaxSpeed"
IT_MinSpeed = "MinSpeed"
IT_Debit_Moyen = "Moyen"
GeneralConfSpec = """
	[{0}]
	# limites du debit vocal
	{1} = integer(default=1, min=1, max= 100)
	{2} = integer(default=60, min=1, max= 100)
		# definit le debit vocal moyen
		# = 0 pour garder le debit vocal en cours
	#  entre minSpeed  et maxSpeed  pour fixer le debit vocal moyen
	{3} = integer(default=25)
	""".format(SCT_General, IT_MinSpeed, IT_MaxSpeed, IT_Debit_Moyen)

# Debit general section items

IT_Gen_Offset = "Offset"

DebitGeneralConfSpec = """
	[{0}]
# definit l'augmentation ou la  diminution du debit vocal general
	# c'est un pourcentage de l''ecart entre   le debit vocal moyen et le debit max
	{1} = integer(default=15, min=1, max= 100)
	""".format(SCT_Debit_General, IT_Gen_Offset)

#  Debit explication items
IT_Expli_Offset = "Offset"
DebitExplicationConfSpec = """
	[{0}]
	# definit l'augmentation du debit vocal courant pour  l'option explication rapide
	# c'est un pourcentage entre le debit vocal moyen et le debit vocal max
	{1} = integer(default=10, min=1, max= 100)
""".format(SCT_Debit_Explication, IT_Expli_Offset)


# debit lesson 14 item
IT_Lesson_14_Offset = "Offset"

DebitLesson14ConfSpec = """
	[{0}]
	# defini la diminution applique au  debit vocal moyen pour les    dictees 14
	# c'est un pourcentage de l'ecart entre le debit vocal moyen et le debit vocal max.
	{1} = integer(default=15, min=1, max= 100)
""".format(SCT_Debit_Lesson_14, IT_Lesson_14_Offset)


# debit lesson 15 item
IT_Lesson_15_Offset = "Offset"

DebitLesson15ConfSpec = """
	[{0}]
	# defini l'augmentation et diminution du debit vocal pour les dictees 15 par rapport au debit vocal moyen
	# c'est un pourcentage  de l'ecart entre le debit vocal moyen et le debit vocal max.
	{1} = integer(default=5, min=1, max= 100)
""".format(SCT_Debit_Lesson_15, IT_Lesson_15_Offset)

# debit Dictee 18  item
IT_Dictee_18_Offset = "Offset"
DebitDictee18ConfSpec = """
	[{0}]
	# defini l'augmentation du debit vocal par rapport au debit vocal moyen
	# c'est un pourcentage de l'ecart entre le debit vocal moyen et le debit vocal max.
	{1} = integer(default=10, min=1, max= 100)
""".format(SCT_Debit_Dictee_18, IT_Dictee_18_Offset)


# debit Dictee 19  item
IT_Dictee_19_Offset = "Offset"
IT_Dictee_19_Increment = "Increment"

DebitDictee19ConfSpec = """
	[{0}]
	# defini le debit de base pour les dictees 19
	# c'est un pourcentage de l'ecart entre le debit vocal moyen et le debit vocal max.
	# il s'ajoute au debit vocal moyen
	{1} = integer(default=15, min=1, max= 100)
	# defini l'augmentation du debit vocal entre les dictees
	# c'est un pourcentage de l'ecart entre le debit vocal moyen et le debit vocal max.
	{2} = integer(default=5, min=1, max= 100)
""".format(SCT_Debit_Dictee_19, IT_Dictee_19_Offset, IT_Dictee_19_Increment)

#: The configuration specification
#: @type: ConfigObj
confspec = ConfigObj(StringIO(
	""" #ApprentiClavier Configuration File
{0}{1}{2}{3}{4}{5}{6}
""".format(GeneralConfSpec, DebitGeneralConfSpec, DebitExplicationConfSpec, DebitLesson14ConfSpec, DebitLesson15ConfSpec, DebitDictee18ConfSpec, DebitDictee19ConfSpec)
), list_values=False, encoding="UTF-8")
confspec.newlines = "\r\n"

#: The active configuration, C{None} if it has not yet been loaded.
#: @type: ConfigObj
conf = None
configFileError = None
addonConfigFolderPath = None
addonConfigFilePath = None


def InitAddonConfigPath():
	global addonConfigFolderPath, addonConfigFilePath
	addonPath = addonHandler.getCodeAddon().path
	addonConfigFolderPath = os.path.join(addonPath, "config")
	addonConfigFilePath = os.path.join(addonPath, "config", "settings.ini")


def Load():
	"""Loads the configuration from the configFile.
	"""

	global conf, configFileError
	InitAddonConfigPath()
	configFileName = addonConfigFilePath
	if not os.path.isdir(addonConfigFolderPath) or not os.path.isfile(addonConfigFilePath):
		conf = ConfigObj(None, configspec=confspec, indent_type="\t", encoding="UTF-8")
		conf.filename = configFileName
		Save()
	try:
		conf = ConfigObj(configFileName, configspec=confspec, indent_type="\t", encoding="UTF-8")
	except ConfigObjError as e:
		conf = ConfigObj(None, configspec=confspec, indent_type="\t", encoding="UTF-8")
		conf.filename = configFileName
		# Translators: message to user to report parsing error.
		configFileError = _("Error parsing ApprentiClavier configuration file: %s") % e

	# Python converts \r\n to \n when reading files in Windows, so ConfigObj can't determine the true line ending.
	conf.newlines = "\r\n"
	val = Validator()
	result = conf.validate(val)
	if not result or configFileError:
		log.warn(configFileError)


def Save():
	"""Saves the configuration to the config file.
	"""
	# We never want to save config if runing securely
	if globalVars.appArgs.secure:
		return
	# We save the configuration, in case the user would not have checked the "Save configuration on exit" checkbox in General settings.
	if not config.conf['general']['saveConfigurationOnExit']:
		return
	global conf
	if not os.path.isdir(addonConfigFolderPath):
		try:
			os.makedirs(addonConfigFolderPath)
		except OSError as e:
			log.warning("Could not create configuration directory")
			log.debugWarning("", exc_info=True)
			raise e
	# Copy default settings and formatting.
	val = Validator()
	try:
		conf.validate(val, copy=True)
	except VdtTypeError:
		# error in configuration file
		log.warning("saveSettings: validator error: %s" % conf.errors)
		return
	try:
		conf.write()
	except:  # noqa:E722
		log.warning("Could not save configuration - probably read only file system")


def getDebitGeneralMoyen():
	return int(conf[SCT_General][IT_Debit_Moyen])


def getDebitGeneralOffset():
	return int(conf[SCT_Debit_General][IT_Gen_Offset])


def getDebitExplicationOffset():
	return int(conf[SCT_Debit_Explication][IT_Expli_Offset])


def getMinAndMaxSpeed():
	min = int(conf[SCT_General][IT_MinSpeed])
	max = int(conf[SCT_General][IT_MaxSpeed])
	return (min, max)


def getDebitDictee14Offset():
	return int(conf[SCT_Debit_Lesson_14][IT_Lesson_15_Offset])


def getDebitDictee15Offset():
	return int(conf[SCT_Debit_Lesson_15][IT_Lesson_15_Offset])


def getDebitDictee18Offset():
	return int(conf[SCT_Debit_Dictee_18][IT_Dictee_18_Offset])


def getDebitDictee19OffsetAndIncrement():
	offset = int(conf[SCT_Debit_Dictee_19][IT_Dictee_19_Offset])
	increment = int(conf[SCT_Debit_Dictee_19][IT_Dictee_19_Increment])
	return (offset, increment)
