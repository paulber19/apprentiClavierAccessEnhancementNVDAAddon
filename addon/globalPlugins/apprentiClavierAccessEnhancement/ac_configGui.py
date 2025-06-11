# globalPlugins\apprentiClavierAccessEnhancement\ac_configGui.py
# a part of aprentiClavierAccessEnhancement add-on
# Copyright 2019-2024,paulber19
# This file is covered by the GNU General Public License.

# manage add-on configuration dialog

import addonHandler
import wx
import gui
from gui.settingsDialogs import SettingsDialog
import os
import sys
_curAddon = addonHandler.getCodeAddon()
_addonSummary = _curAddon.manifest['summary']
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from ac_addonConfigManager import _addonConfigManager
del sys.path[-1]
addonHandler.initTranslation()


class ApprentiClavierSettingsDialog(SettingsDialog):
	# Translators: This is the label for the ApprentiClaviery settings  dialog.
	title = _("%s - settings") % _addonSummary

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a group of editing options in the ApprentiClavier settings panel.
		groupText = _("Update")
		group = gui.guiHelper.BoxSizerHelper(
			self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=groupText), wx.VERTICAL))
		sHelper.addItem(group)
		# Translators: This is the label for a checkbox in the ApprentiClavier SettingsDialog.
		labelText = _("Automatically check for &updates")
		self.autoCheckForUpdatesCheckBox = group.addItem(wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.autoCheckForUpdatesCheckBox.SetValue(_addonConfigManager.toggleAutoUpdateCheck(False))
		# Translators: This is the label for a checkbox in the ApprentiClavier settings panel.
		labelText = _("Update also release versions to &developpement versions")
		self.updateReleaseVersionsToDevVersionsCheckBox = group.addItem(
			wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.updateReleaseVersionsToDevVersionsCheckBox.SetValue(
			_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))
		# translators: label for a button in ApprentiClavier settings panel.
		labelText = _("&Check for update")
		checkForUpdateButton = wx.Button(self, label=labelText)
		group.addItem(checkForUpdateButton)
		checkForUpdateButton.Bind(wx.EVT_BUTTON, self.onCheckForUpdate)
		# translators: this is a label for a button in update settings panel.
		labelText = _("View &history")
		seeHistoryButton = wx.Button(self, label=labelText)
		group.addItem(seeHistoryButton)
		seeHistoryButton.Bind(wx.EVT_BUTTON, self.onSeeHistory)

	def onCheckForUpdate(self, evt):
		from .updateHandler import addonUpdateCheck
		self.saveSettingChanges()
		releaseToDevVersion = self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked()
		wx.CallAfter(addonUpdateCheck, auto=False, releaseToDev=releaseToDevVersion)
		self.Close()

	def postInit(self):
		self.autoCheckForUpdatesCheckBox.SetFocus()

	def onSeeHistory(self, evt):
		addon = addonHandler.getCodeAddon()
		from languageHandler import getLanguage
		curLang = getLanguage()
		theFile = os.path.join(addon.path, "doc", curLang, "changes.html")
		if not os.path.exists(theFile):
			lang = curLang.split("_")[0]
			theFile = os.path.join(addon.path, "doc", lang, "changes.html")
			if not os.path.exists(theFile):
				lang = "en"
				theFile = os.path.join(addon.path, "doc", lang, "changes.html")
		os.startfile(theFile)

	def saveSettingChanges(self):
		if self.autoCheckForUpdatesCheckBox.IsChecked() != _addonConfigManager .toggleAutoUpdateCheck(False):
			_addonConfigManager .toggleAutoUpdateCheck(True)
			from . updateHandler.update_check import setCheckForUpdate
			setCheckForUpdate(_addonConfigManager.toggleAutoUpdateCheck(False))
		if self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked() != (
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions(False)):
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions(True)

	def onOk(self, evt):
		self.saveSettingChanges()
		super(ApprentiClavierSettingsDialog, self).onOk(evt)
