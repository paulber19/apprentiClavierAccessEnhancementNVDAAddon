# globalPlugins\apprentiClavierAccessEnhancement\ac_globalPlugin.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright (C) 2019-2024 Paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import globalPluginHandler
import gui
import wx
import os
import sys
addon = addonHandler.getCodeAddon()
path = os.path.join(addon.path, "shared")
sys.path.append(path)
from ac_addonConfigManager import _addonConfigManager
del sys.path[-1]
addonHandler.initTranslation()


class ApprentiClavierGlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(ApprentiClavierGlobalPlugin, self).__init__(*args, **kwargs)
		self.installSettingsMenu()
		from .updateHandler.update_check import setCheckForUpdate
		setCheckForUpdate(_addonConfigManager.toggleAutoUpdateCheck(False))
		from . updateHandler import autoUpdateCheck
		autoUpdateCheck(releaseToDev=_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))

	def installSettingsMenu(self):
		self.preferencesMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
		from .ac_configGui import ApprentiClavierSettingsDialog
		self.menu = self.preferencesMenu.Append(
			wx.ID_ANY,
			ApprentiClavierSettingsDialog.title + " ...",
			"")
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onMenu, self.menu)

	def deleteSettingsMenu(self):
		try:
			self.preferencesMenu.Remove(self.menu)
		except Exception:
			pass

	def terminate(self):
		self.deleteSettingsMenu()
		super(ApprentiClavierGlobalPlugin, self).terminate()

	def onMenu(self, evt):
		from .ac_configGui import ApprentiClavierSettingsDialog
		from versionInfo import version_year, version_major
		if [version_year, version_major] >= [2024, 1]:
			gui.mainFrame.popupSettingsDialog(ApprentiClavierSettingsDialog)
		else:
			gui.mainFrame._popupSettingsDialog(ApprentiClavierSettingsDialog)
