# -*- coding: iso-8859-15 -*-
# appModules\apprenticlavier\ac_voiceControl.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright (C) 2019- 2022, Paulber19
# This file is covered by the GNU General Public License.


import addonHandler
from logHandler import log
from characterProcessing import SymbolLevel
SYMLVL_SOME = SymbolLevel.SOME
SYMLVL_ALL = SymbolLevel.ALL
import config
import globalVars
import api
from controlTypes.state import State
STATE_CHECKED = State.CHECKED
from . import ac_config
from synthDriverHandler import getSynth, setSynth

addonHandler.initTranslation()

# voice options constants
V_RATE = 1

# the voiceControl object
mainVoiceControl = None
# memorise les options de l'utilisateur
GB_userOptions = {}


def getUserOptions():
	global GB_userOptions
	obj = api.getForegroundObject().parent
	try:
		oOptions = obj.children[2].children[1].firstChild
		o = oOptions.children[1]
	except Exception:
		log.warning("Menu options not available")
		return

	GB_userOptions = {}
	while o:
		try:
			state = False
			if STATE_CHECKED in o.states:
				state = True
			if o.name is not None and len(o.name) > 0:
				GB_userOptions[o.name] = state

			o = o.next
		except Exception:
			o = None


class SpeedRateVoiceControl(object):
	def __init__(self):
		self.rateSetting = self.getSetting()


	def getSetting(self):
		settings = globalVars.settingsRing.settings
		for setting in settings:
			id = setting.setting.id
			if id == "rate":
				return setting
		return None
	def getValue(self):
		synthName = getSynth().name
		rate = config.conf["speech"][synthName]["rate"]
		return rate


	def setValue(self, value):
		if self.getValue() == value:
			return
		log.debug("new rate: %s" %value)
		synth = getSynth()
		config.conf["speech"][synth.name]["rate"] = value
		synth.rate = value
		globalVars.settingsRing.updateSupportedSettings(synth)


	def getCurrentSetting(self):
		min = self.rateSetting.min
		max = self.rateSetting.max
		speedRate = self.getValue()
		return (speedRate, min, max)


class VoiceControl:
	def __init__(self):

		self.speedRateVoiceControl = SpeedRateVoiceControl()
		self.currentSetting = {}
		self.initialize()

	def initialize(self):
		self.saveCurrentSettings()
		# debit moyen  de base réglée au debit  utilisateur en cours
		self.userSpeed = self.setting["speedRate"]
		if ac_config.getDebitGeneralMoyen() != 0:
			# la configuration prevoit un debit moyen  par defaut
			self.userSpeed = ac_config.getDebitGeneralMoyen()
		self.OffGenCourant = 0
		self.OffExpliCourant = 0

		(minSpeed, maxSpeed) = ac_config.getMinAndMaxSpeed()
		# OffExpli-OffsetGen sont utilisés par les options "Debit Explications" et "Debit General".
		# il sont definis dans le fichier de configuration en pourcentage
		delta = maxSpeed - self.userSpeed
		self.OffGen = (delta * ac_config.getDebitGeneralOffset()) / 100
		self.OffExpli = (delta * ac_config.getDebitExplicationOffset()) / 100
		self.offDictee14 = (delta * ac_config.getDebitDictee14Offset()) / 100
		self.offDictee15 = (delta * ac_config.getDebitDictee15Offset()) / 100
		self.offDictee18 = (delta * ac_config.getDebitDictee18Offset()) / 100
		(self.offDictee19, self.incDictee19) = ac_config.getDebitDictee19OffsetAndIncrement()
		self.offDictee19 = (delta * self.offDictee19) / 100
		self.incDictee19 = (delta * self.incDictee19) / 100
		# echo caractere et Peu de ponctuations en entrant dans ApprentiClavier
		self.setTypingEcho(1)
		self.setPunctuationLevel(1)
		# vitesse de la voix  moyenne
		self.ValueVoiceSetting(V_RATE, self.userSpeed + self.OffGenCourant)

	def terminate(self):
		self.restoreCurrentSettings()

	def saveCurrentSettings(self):
		self.setting = {}
		self.setting["speakTypedCharacters"] = config.conf["keyboard"]["speakTypedCharacters"]
		self.setting["speakTypedWords"] = config.conf["keyboard"]["speakTypedWords"]
		self.setting["symbolLevel"] = config.conf["speech"]["symbolLevel"]
		self.setting["speedRate"] = self.speedRateVoiceControl.getValue()

	def restoreCurrentSettings(self):
		config.conf["keyboard"]["speakTypedCharacters"] = self.setting["speakTypedCharacters"]
		config.conf["keyboard"]["speakTypedWords"] = self.setting["speakTypedWords"]
		config.conf["speech"]["symbolLevel"] = self.setting["symbolLevel"]
		self.speedRateVoiceControl.setValue(self.setting["speedRate"])

	def setOffsetGenEtExpliCourants(self, windowName):
		# on retrouve les options debit general et debit explication avec le titre des fenetres menu principal
		# et sous menu menu lecon
		# comme suit:
		# si titre = "Normal." ou titre commence psans blanc: debit explication normal
		# si titre  = "Rapide." ou il commence par 3 blanc: debit explication rapide
		# si titre == "Lent." ou 1 blanc apres menu: debit general lent
		# si titre == "Moyen." ou deux blancs: debit general moyen
		# si titre == "Vite." ou 3 blancs apres menu : debit general vite
		# pour  debit explication
		if "Rapide." in windowName[:7]:
			# explication rapide
			self.OffExpliCourant = self.OffExpli
			return
		if "Normal." in windowName[:7]:
			# explication normal
			self.OffExpliCourant = 0
			return
		# pour debit general
		if "Vite." in windowName[:5]:
			# debit general vite
			self.OffGenCourant = self.OffGen
			return
			if "Moyen." in windowName[:6]:
				# debit  general moyen
				self.OffGenCourant = 0
				return
		# en tenant compte de la forme du titre de l'arboressence des menus
		temp = windowName.lstrip()
		if "Menu " in temp[:5]:
			self.OffExpliCourant = 0
			if "   " in windowName[:3]:
				# debit explication rapide
				self.OffExpliCourant = self.OffExpli
			if "Menu   " in temp[:7]:
				# debit general rapide
				self.OffGenCourant = self.OffGen
			elif "Menu  " in temp[:7]:
				# debit general moyen
				self.OffGenCourant = 0
			else:
				# debit general lent
				self.OffGenCourant = 0 - self.OffGen

	def updateVoiceSettings(self, windowName, windowText):
		log.debug("updateVoiceSettings: %s" % windowName)
		self.setOffsetGenEtExpliCourants(windowName)
		# Vitesse vocalisation, et ponctuation, selon la mise en forme du titre de la fenêtre
		# par defaut, vitesse, ponctuation STANDARD (
		self.MemoSpeed = self.userSpeed + self.OffGenCourant
		punctuation = 1
		typingEcho = 0
		# pour fenêtre "bienvenue"
		if "Bienvenue" in windowName:
			typingEcho = 1
	# pour page explicative sans nom
		elif (windowName == "") and (u"pressez espace pour répéter" in windowText.lower()):
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.OffExpliCourant

		# Pour page explicatives identifiee
		elif ("Page" in windowName.lstrip()[:4]):
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.OffExpliCourant

		# Pour les  "dictées 14
		# on baisse le debit
		elif u"Dictée 14" in windowName[:9]:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant - self.offDictee14

		elif u"Leçon 14" in windowName[:8]:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant - self.offDictee14
			punctuation = 4
		# Pour les  "dictées 15
		elif u"Dictée 15 A" in windowName[:11]:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant - self.offDictee15
		elif u"Leçon 15 A" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant - self.offDictee15
			punctuation = 4
		elif u"Dictée 15 B" in windowName:
			pass
		elif u"Leçon 15 B" in windowName:
			punctuation = 4
		elif u"Dictée 15 C" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee15

		elif u"Leçon 15 C" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourantt + self.offDictee15
			punctuation = 4
		# Pour la leçon 18D
		elif u"Leçon 18 D" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee18
		# Pour les  dictées 19
		elif u"Dictée 19 A" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19

		elif u"Leçon 19 A" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19
			punctuation = 4
		elif u"Dictée 19 B" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19 + self.incDictee19

		elif u"Leçon 19 B" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19 + self.incDictee19
			punctuation = 4
		elif u"Dictée 19 C" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19 + 2 * self.incDictee19

		elif u"Leçon 19 C" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19 + 2 * self.incDictee19
			punctuation = 4
		elif u"Dictée 19 D" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19 + 3 * self.incDictee19

		elif u"Leçon 19 D" in windowName:
			self.MemoSpeed = self.userSpeed + self.OffGenCourant + self.offDictee19 + 3 * self.incDictee19
			punctuation = 4
		# on positionne le debit, la ponctuation et l'echo caractere
		self.ValueVoiceSetting(V_RATE, int(self.MemoSpeed))
		self.setPunctuationLevel(punctuation)
		self.setTypingEcho(typingEcho)

	def ValueVoiceSetting(self, iSetting, ValidValue):

		(speedRate, minRate, maxRate) = self.getSettingInformation(iSetting)
		speedRate = int(ValidValue * (maxRate - minRate) / 100)
		if (speedRate < minRate):
			speedRate = minRate
		elif (speedRate > maxRate):
			speedRate = maxRate
		self.setVoiceSetting(iSetting, speedRate)

	def getSettingInformation(self, iSetting):
		if iSetting == V_RATE:
			return self.speedRateVoiceControl.getCurrentSetting()

	def setVoiceSetting(self, iSetting, value):
		if iSetting == V_RATE:
			self.speedRateVoiceControl.setValue(value)

	def setPunctuationLevel(self, levelValue):
		if levelValue == 1:
			level = SYMLVL_SOME
		elif levelValue == 4:
			level = SYMLVL_ALL
		else:
			return
		config.conf["speech"]["symbolLevel"] = level

	def setTypingEcho(self, echo):
		try:
			from config.configFlags import TypingEcho
			value = TypingEcho.OFF.value
		except ImportError:
			value = False
		# word echo off
		config.conf["keyboard"]["speakTypedWords"] = value
		if echo == 0:
			# char echo off
			config.conf["keyboard"]["speakTypedCharacters"] = value
		elif echo == 1:
			# characterecho on
			config.conf["keyboard"]["speakTypedCharacters"] = value


def initialize():
	global mainVoiceControl
	ac_config.Load()
	mainVoiceControl = VoiceControl()


def terminate():
	global mainVoiceControl
	if mainVoiceControl is not None:
		mainVoiceControl.terminate()
		mainVoiceControl = None


def updateSettings(obj, windowText=""):
	if mainVoiceControl is None:
		return

	windowName = obj.name
	if windowName is None:
		windowName = ""
	mainVoiceControl.updateVoiceSettings(windowName, windowText)
