# appModules\apprenticlavier\ac_configManager.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright 2019-2025,paulber19
# This file is covered by the GNU General Public License.

from logHandler import log
import addonHandler
import os
import globalVars
import wx
import gui
import config
from configobj import ConfigObj
from configobj.validate import Validator, ValidateError
from io import StringIO

addonHandler.initTranslation()

# config section
SCT_General = "General"

# general section items
ID_ConfigVersion = "ConfigVersion"
ID_AutoUpdateCheck = "AutoUpdateCheck"
ID_UpdateReleaseVersionsToDevVersions = "UpdateReleaseVersionsToDevVersions"

_curAddon = addonHandler.getCodeAddon()
_addonName = _curAddon.manifest["name"]


def renameFile(file, dest):
	try:
		if os.path.exists(dest):
			os.remove(dest)
		os.rename(file, dest)
		log.debug("current configuration file: %s renamed to : %s" % (file, dest))
	except Exception:
		log.error("current configuration file: %s  cannot be renamed to: %s" % (file, dest))


class BaseAddonConfiguration(ConfigObj):
	_version = ""
	""" Add-on configuration file. It contains metadata about add-on . """
	_GeneralConfSpec = """[{section}]
	{idConfigVersion} = string(default = " ")
	""".format(section=SCT_General, idConfigVersion=ID_ConfigVersion)
	configspec = ConfigObj(StringIO("""# addon Configuration File
	{general}""".format(general=_GeneralConfSpec)
	), list_values=False, encoding="UTF-8")

	def __init__(self, input):
		""" Constructs an L{AddonConfiguration} instance from manifest string data
		@param input: data to read the addon configuration information
		@type input: a fie-like object.
		"""
		super(BaseAddonConfiguration, self).__init__(
			input, configspec=self.configspec, encoding='utf-8', default_encoding='utf-8')
		self.newlines = "\r\n"
		self._errors = []
		val = Validator()
		result = self.validate(val, copy=True, preserve_errors=True)
		if type(result) is dict:
			self._errors = self.getValidateErrorsText(result)
		else:
			self._errors = None

	def getValidateErrorsText(self, result):
		textList = []
		for name, section in result.items():
			if section is True:
				continue
			textList.append("section [%s]" % name)
			for key, value in section.items():
				if isinstance(value, ValidateError):
					textList.append(
						'key "{}": {}'.format(
							key, value))
		return "\n".join(textList)

	@property
	def errors(self):
		return self._errors


class AddonConfiguration10(BaseAddonConfiguration):
	_version = "1.0"
	_GeneralConfSpec = """[{section}]
	{configVersion} = string(default = {version})
	{autoUpdateCheck} = boolean(default=True)
	{updateReleaseVersionsToDevVersions} = boolean(default=False)
	""".format(
		section=SCT_General,
		configVersion=ID_ConfigVersion,
		version=_version, autoUpdateCheck=ID_AutoUpdateCheck,
		updateReleaseVersionsToDevVersions=ID_UpdateReleaseVersionsToDevVersions)

	#: The configuration specification
	configspec = ConfigObj(StringIO(
		"""# addon Configuration File
{general}
""".format(general=_GeneralConfSpec)
	), list_values=False, encoding="UTF-8")


PREVIOUSCONFIGURATIONFILE_SUFFIX = ".prev"
DELETECONFIGURATIONFILE_SUFFIX = ".delete"


class AddonConfigurationManager():
	_currentConfigVersion = "1.0"
	_versionToConfiguration = {
		"1.0": AddonConfiguration10,
	}

	def __init__(self):
		self.configFileName = "%sAddon.ini" % _addonName
		self.loadSettings()
		config.post_configSave.register(self.handlePostConfigSave)

	def warnConfigurationReset(self):
		from .messages import alert
		wx.CallLater(
			100,
			alert,
			# Translators: A message warning configuration reset.
			_(
				"The configuration file of the add-on contains errors. "
				"The  configuration has been reset to factory defaults"),
			# Translators: title of message box
			"{addon} - {title}" .format(addon=_curAddon.manifest["summary"], title=_("Warning")),
			wx.OK | wx.ICON_WARNING
		)

	def loadSettings(self):
		userConfig = globalVars.appArgs.configPath
		self.addonConfigFile = addonConfigFile = os.path.join(userConfig, self.configFileName)
		self.oldConfigFile = addonConfigFile + PREVIOUSCONFIGURATIONFILE_SUFFIX
		# after add-on installation and and the user does not want to keep the configuration
		# the configuration has been renamed with .delete extension
		# if this file exists, it must be deleted
		self.deleteConfigFile = self.addonConfigFile + DELETECONFIGURATIONFILE_SUFFIX
		if os.path.exists(self.deleteConfigFile):
			os.remove(self.deleteConfigFile)
		doMerge = True
		if os.path.exists(addonConfigFile):
			# there is allready a config file
			try:
				baseConfig = BaseAddonConfiguration(addonConfigFile)
				if baseConfig.errors:
					e = Exception("Error parsing configuration file:\n%s" % baseConfig.errors)
					raise e
				if baseConfig[SCT_General][ID_ConfigVersion] != self._currentConfigVersion:
					# it's an old config, but old config file must not exist here.
					# Must be deleted
					os.remove(addonConfigFile)
					log.warning(
						"%s: Old configuration version found. Config file is removed: %s" % (_addonName, addonConfigFile))
				else:
					# it's the same version of config, so no merge
					doMerge = False
			except Exception as e:
				log.warning(e)
				# error on reading config file, so delete it
				os.remove(addonConfigFile)
				self.warnConfigurationReset()
				log.warning(
					"%s Addon configuration file error: configuration reset to factory defaults" % _addonName)

		if os.path.exists(addonConfigFile):
			self.addonConfig =\
				self._versionToConfiguration[self._currentConfigVersion](addonConfigFile)
			if self.addonConfig.errors:
				log.warning(self.addonConfig.errors)
				log.warning(
					"%s Addon configuration file error: configuration reset to factory defaults" % _addonName)
				os.remove(addonConfigFile)
				self.warnConfigurationReset()
				# reset configuration to factory defaults
				self.addonConfig =\
					self._versionToConfiguration[self._currentConfigVersion](None)
				self.addonConfig.filename = addonConfigFile
				doMerge = False
		else:
			# no add-on configuration file found
			self.addonConfig =\
				self._versionToConfiguration[self._currentConfigVersion](None)
			self.addonConfig.filename = addonConfigFile
		# merge step
		if os.path.exists(self.oldConfigFile):
			if doMerge:
				self.mergeSettings(self.oldConfigFile)
			os.remove(self.oldConfigFile)
		if not os.path.exists(addonConfigFile):
			self.saveSettings(True)

	def mergeSettings(self, previousConfigFile):
		baseConfig = BaseAddonConfiguration(previousConfigFile)
		previousVersion = baseConfig[SCT_General][ID_ConfigVersion]
		if previousVersion not in self._versionToConfiguration:
			log.warning("%s: Configuration merge error: unknown previous configuration version number" % _addonName)
			return
		previousConfig = self._versionToConfiguration[previousVersion](previousConfigFile)
		if previousVersion == self.addonConfig[SCT_General][ID_ConfigVersion]:
			# same config version, update data from previous config
			self.addonConfig.update(previousConfig)
			log.warning(
				"%s: Configuration updated with previous configuration file" % _addonName)
			return
		# different config version, so do a  merge with previous config.
		try:
			self.addonConfig.mergeWithPreviousConfigurationVersion(previousConfig)
		except Exception:
			pass

	def canConfigurationBeSaved(self, force):
		# Never save config or state if running securely or if running from the launcher.
		try:
			# for NVDA version >= 2023.2
			from NVDAState import shouldWriteToDisk
			writeToDisk = shouldWriteToDisk()
		except ImportError:
			# for NVDA version < 2023.2
			writeToDisk = not (globalVars.appArgs.secure or globalVars.appArgs.launcher)
		if not writeToDisk:
			log.debug("Not writing add-on configuration, either --secure or --launcher args present")
			return False
		# after add-on installation and and the user does not want to keep the configuration
		# the configuration has been renamed with .delete extension
		# if this file exists, configuration should not be saved
		if os.path.exists(self.deleteConfigFile):
			return False
		# after an add-on removing, configuration is deleted
		# so  don't save configuration if there is no nvda restart
		if _curAddon.isPendingRemove:
			return False
		# We don't save the configuration, in case the user
			# would not have checked the "Save configuration on exit
			# " checkbox in General settings and force is False
		if not force and not config.conf['general']['saveConfigurationOnExit']:
			return False
		return True

	def saveSettings(self, force=False):
		if self.addonConfig is None:
			return
		if not self.canConfigurationBeSaved(force):
			return
		try:
			val = Validator()
			self.addonConfig.validate(val, copy=True)
			self.addonConfig.write()
			log.warning("%s: configuration saved" % _addonName)
			# if an installation took place, the configuration file was renamed.
			# so you have to do the same thing after saving
			if os.path.exists(self.oldConfigFile):
				renameFile(self.addonConfigFile, self.oldConfigFile)
		except Exception:
			log.warning("%s: Could not save configuration - probably read only file system" % _addonName)

	def handlePostConfigSave(self):
		self.saveSettings(True)

	def terminate(self):
		self.saveSettings()

	def toggleGeneralOption(self, id, toggle):
		conf = self.addonConfig
		if toggle:
			conf[SCT_General][id] = not conf[SCT_General][id]
			self.saveSettings()
		return conf[SCT_General][id]

	def toggleAutoUpdateCheck(self, toggle=True):
		return self.toggleGeneralOption(ID_AutoUpdateCheck, toggle)

	def toggleUpdateReleaseVersionsToDevVersions(self, toggle=True):
		return self.toggleGeneralOption(ID_UpdateReleaseVersionsToDevVersions, toggle)


# singleton for addon config manager
_addonConfigManager = AddonConfigurationManager()
