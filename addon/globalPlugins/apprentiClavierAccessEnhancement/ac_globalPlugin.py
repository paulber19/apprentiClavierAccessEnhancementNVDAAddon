# globalPlugins\apprentiClavierAccessEnhancement\ac_globalPlugin.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright (C) 2019 Paulber19
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
from ac_addonConfigManager import _addonConfigManager  # noqa:E402
del sys.path[-1]
addonHandler.initTranslation()


class ApprentiClavierGlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(ApprentiClavierGlobalPlugin, self).__init__(*args, **kwargs)
		self.installSettingsMenu()
		from . updateHandler import autoUpdateCheck
		if _addonConfigManager.toggleAutoUpdateCheck(False):
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
			if wx.version().startswith("4"):
				# for wxPython 4
				self.preferencesMenu.Remove(self.menu)
			else:
				# for wxPython 3
				self.preferencesMenu.RemoveItem(self.menu)
		except:  # noqa:E722
			pass

	def terminate(self):
		self.deleteSettingsMenu()
		super(ApprentiClavierGlobalPlugin, self).terminate()

	def onMenu(self, evt):
		from .ac_configGui import ApprentiClavierSettingsDialog
		gui.mainFrame._popupSettingsDialog(ApprentiClavierSettingsDialog)
