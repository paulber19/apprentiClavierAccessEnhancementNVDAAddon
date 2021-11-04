# -*- coding: iso-8859-15 -*-
# appModules\aprenticlavier\___init__.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright (C) 2019-2021, Paulber19
# This file is covered by the GNU General Public License.

import addonHandler
from logHandler import log
import globalVars
import appModuleHandler
try:
	# for nvda version >= 2021.2
	from characterProcessing import SymbolLevel
	SYMLVL_ALL = SymbolLevel.ALL
except ImportError:
	from characterProcessing import SYMLVL_ALL
import speech
import ui
import api
import wx
from keyboardHandler import KeyboardInputGesture
from NVDAObjects.window import Window, DisplayModelEditableText
from NVDAObjects.window.edit import UnidentifiedEdit
from editableText import EditableText
from oleacc import *  # noqa:F403
from IAccessibleHandler import accNavigate
import config
try:
	# for nvda version >= 2021.2
	from controlTypes.state import State
	STATE_INVISIBLE  = State.INVISIBLE 
except ImportError:
	from controlTypes import STATE_INVISIBLE
from . import ac_voiceControl
from .ac_lessonsMode import *  # noqa:F403
addon = addonHandler.getCodeAddon()

addonHandler.initTranslation()


# a global timer  for  delay task
GB_timer = None
GB_speakTypeCharacter = None
GB_precObjID = None
# for debugging
GB_traceMode = False

#  to know if .module hasà focus
GB_moduleHasFocus = False
GB_inGetTopLevelFunction = 0

score_keyHelp_timer = {
	# lesson: score, f2 key help timer, timer
	"1a,1B,1c,1d": (2, 5, -1),
	"99a,2a,2b,2c,2e,3a,3b,4a,4b,4c,4d,4e,4f,4g,4h,5a,5b,5c,8b,8c,8d,8e,8f,8h,9a,9b,9c,9d,10a,10b,10c,13g,16a,16c,17a,18a,18b,18c,18e": (1, 4, -1),
	"2d,2f,2g,2h,3c": (3, 6, -1),
	"6a,6b,6c,6d": (4, 5, 3),
	"7a,7b,7c,11a,11b,11c,18d": (3, 5, 3),
	"8a,12a,12b,12c,12d,13a,13b,13c,16b,16d": (2, 5, -1),
	"8g,13d,13e,13f,17b,17c,17d": (2, 6, -1),
	"14a,14b,14c,15a,15b,15c,19a,19b,19c,19d": (2, 4, -1)
	}


def printDebug(text):
	if GB_traceMode:
		log.info(text)
	return


def TrapAltOrWindowsKey(gesture):
	if "alt" in gesture._get_modifierNames():
		KeyboardInputGesture.fromName("control").send()
	if "windows" in gesture._get_modifierNames():
		KeyboardInputGesture.fromName("windows").send()
		KeyboardInputGesture.fromName("control").send()


def GetTopLevelObject(obj=None):
	global GB_inGetTopLevelFunction
	GB_inGetTopLevelFunction += 1
	if obj is None:
		o = api.getFocusObject()
	else:
		o = obj
	while o is not None:
		oTop = o
		try:
			o = o.parent
			if o.name and o.name.lower() == "bureau":
				o = None
		except:  # noqa:E722
			printDebug("getTopLevelObject: no parent")
			o = None
	GB_inGetTopLevelFunction -= 1
	return oTop


def StopTimer(timer=None):
	global GB_timer
	printDebug("StopTimer")
	if timer is None:
		timer = GB_timer
	if timer is not None:
		timer.Stop()
		timer = None


def GetObjectId(obj):
	i = 0
	try:
		o = obj.IAccessibleObject.accParent
	except:  # noqa:E722
		return 0
	while o is not None:
		i = i+1
		try:
			(o, childID) = accNavigate(o, 0, NAVDIR_PREVIOUS)
		except:  # noqa:E722
			o = None

	return i


def SayValue(value):

	if value is None:
		return
	value = value.strip("\n\r")
	value = value.strip(u" ")
	if len(value):
		printDebug("SayValue: %s" % value)
		ac_voiceControl.updateSettings(api.getForegroundObject(), value)
		ui.message(value)


def SayText(sText1, sText2, sText3):
	curLevel = config.conf["speech"]["symbolLevel"]
	config.conf["speech"]["symbolLevel"] = SYMLVL_ALL
	speech.cancelSpeech()
	d = {u"à": "a accent grave", "y": u"i grèque", " ": "espace"}
	if len(sText1) > 0:
		# printDebug("sText1 len %s" %len(sText1))
		speech.speakMessage(sText1)
		time.sleep(0.2)

	if len(sText2) > 0:
		if len(sText2) == 1 and sText2 in d.keys():
			sText2 = d[sText2]
		# printDebug("sText1 len %s" %len(sText2))
		speech.speakMessage(sText2)
		time.sleep(0.2)

	if len(sText3) > 0:
		if len(sText3) == 1 and sText3 in d.keys():
			sText3 = d[sText3]
		elif len(sText3) == 1 and ("A" <= sText3 and sText3 <= "Z"):
			sText3 = sText3.lower() + " majuscule"
		# printDebug("sText3 len %s" %len(sText3))
		speech.speakMessage(sText3)

	printDebug("SayText %s, %s, %s" % (sText1, sText2, sText3))
	config.conf["speech"]["symbolLevel"] = curLevel


def DireInfosTemporisee(obj, timer):
	global GB_timer

	StopTimer(GB_timer)
	printDebug("DireInfoTemporisee %s" % timer)
	GB_timer = wx.CallLater(timer, obj.DireInfos)


def GetLessonIdentifier(obj):
	oTop = GetTopLevelObject(obj)
	name = oTop.name
	if name is None:
		return 0
	if u"leçon " not in name.lower():
		if u"exercice" in name.lower():
			return EXERCICES_LESSON_IDENTIFIER
		return 0

	identifier = name[6:].replace(".", "")
	return identifier.split(" ")


def getLessonMode(obj, sATaper=""):
	identifier = (num, letter) = GetLessonIdentifier(obj)
	if identifier == 0:
		# printDebug("getLessonMode mode indetermine")
		return 0
	try:
		mode = lessonToMode[num]
	except:  # noqa:E722
		try:
			mode = lessonToMode["".join((num, letter.lower()))]
		except:  # noqa:E722
			mode = 0

	return mode


def getATaperInfos():
	try:
		oForeground = api.getTopLevelObject().IAccessibleObject
		(o, childId) = accNavigate(oForeground, 0, NAVDIR_LASTCHILD)
	except:  # noqa:E722
		return ""
	if o.accState(0) & STATE_SYSTEM_INVISIBLE:
		printDebug("getATAperInfo sans info")
		return ""
	(o1, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
	if o1.accState(0) & STATE_SYSTEM_INVISIBLE:
		printDebug("getATaperInfo state invisible ")
		return ""
	sATaper = o1.accValue(0)
	if sATaper is None:
		printDebug(" getATaperInfo pas d'info a taper")
		return ""
	return sATaper


def getScoreControlID():
	# le score se trouve dans la premier fenetre visible qui n'est pas un  timer
	obj = api.getForegroundObject()
	o = obj.firstChild
	while o:
		if (STATE_INVISIBLE not in o.states) and (o.windowClassName == "ThunderRTTextBox"):
			return o.windowControlID
		o = o.next
	return -1


def getATaperAndDejaTapeControlID():
	oDeb = api.getForegroundObject()
	if (oDeb is None) or len(oDeb.children) < 2:
		return(-1, -1)
	o = oDeb.lastChild
	if o:
		controlID = o.windowControlID
		return (controlID, controlID-1)
	return (-1, -1)


def getScoreAndKeyHelpControlID(obj):
	identifier = GetLessonIdentifier(obj)
	if identifier == 0:
		return (-1, -1)
	for key in score_keyHelp_timer.keys():
		tempList = key.lower().split(",")
		if "".join(identifier).lower() in tempList:
			(scoreControlID, keyHelpControlID, timerControlID) = score_keyHelp_timer[key]
			return (scoreControlID, keyHelpControlID, )
	return (-1, -1)


class WindowEx (Window):
	def initOverlayClass(self):
		self.bindGesture("kb:Enter", "EnterKey")

	def script_EnterKey(self, gesture):
		gesture.send()


class InPageWindow(WindowEx):
	def event_valueChange(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("In event_valueChange InPageWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		StopTimer()
		GB_timer = wx.CallLater(100, SayValue, self.value)
		printDebug("Out event_valueChange InPageWindow")

	def event_gainFocus(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("In event_gainFocus InPageWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		if api.getFocusDifferenceLevel() == 1:
			SayValue(api.getForegroundObject().name)
		StopTimer()
		GB_timer = wx.CallLater(100, SayValue, self.value)
		printDebug("Out event_gainFocus InPageWindow")

	def event_caret(self):
		pass


class InAideMemoireWindow(WindowEx):
	def event_valueChange(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("In event_valueChange InAideMemoireWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		if controlID == 3:
			# eviter la repetition
			StopTimer(GB_timer)
			GB_timer = wx.CallLater(100, ui.message, self.value)

		printDebug("Out event_valueChange InAideMemoireWindow")

	def event_gainFocus(self):
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("In event_gainFocus InAideMemoireWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		speech.cancelSpeech()
		if controlID == 0:
			pass

		elif controlID == 6:
			SayValue(api.getForegroundObject().name + "Tapez:")
		printDebug("Out event_gainFocus InAideMemoireWindow")


class InOtherWindow(Window):
	def event_valueChange(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("In event_valueChange InOtherWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		if self.value is not None and len(self.value) or controlID == 5:
			StopTimer(GB_timer)
		GB_timer = wx.CallLater(200, SayValue, self.value)
		printDebug("Out event_valueChange InOtherWindow")

	def event_gainFocus(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("In event_gainFocus InOtherWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		if controlID == 5:
			StopTimer(GB_timer)
		GB_timer = wx.CallLater(200, SayValue, self.value)

		printDebug("Out event_gainFocus InOtherWindow")

	def event_caret(self):
		pass


class InBienvenueWindow(Window):
	def _get_name(self):
		if self.role == 9:  # bouton quitter
			return u"Quitter"

		return super(InBienvenueWindow, self)._get_name()

	def event_caret(self):
		objID = GetObjectId(self)
		controlID = self.windowControlID
		printDebug("In event_caret InBienvenueWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		# super(InBienvenueWindow, self).event_caret()

	def event_valueChange(self):
		objID = GetObjectId(self)
		controlID = self.windowControlID
		printDebug("In event_valueChange InBienvenueWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		if (self.value is None) or (len(self.value) == 0):
			pass

		elif self.role == 8 and GetObjectId(self) in [1, 3]:
			SayValue(self.value)
		elif self.role == 8 and objID == 2:
			SayValue(self.value[-1:])
		else:
			super(InBienvenueWindow, self).event_valueChange()
		printDebug("out event_valueChange InBienvenueWindow")

	def event_gainFocus(self):
		objID = GetObjectId(self)
		controlID = self.windowControlID
		printDebug("In event_gainFocus InBienvenueWindow controlID %s, objID %s, role %s,value %s" % (controlID, objID, self.role, self.value))
		if controlID == 7:
			SayValue(u"taper votre nom, ou simplement Entrée")
			ui.message(self.value)
		elif controlID == 3:
			SayValue(u"Retaper votre nom")
			SayValue(self.value)
		elif controlID == 6:
			SayValue("Quitter")
		elif controlID == 5 and (self.value is None or len(self.value) == 0):
			# pour dire bienvenue au lancement du programme
			pass
		else:
			SayValue(self.parent.name)
			SayValue(self.windowText)
		printDebug("Out event_gainFocus InBienvenueWindow")


class InLessonWindow(Window):
	def event_typedCharacter(self, ch):
		printDebug("event_typedCharacter in InLessonWindow: ch = %s" % ch)
		StopTimer(GB_timer)
		return super(InLessonWindow, self).event_typedCharacter(ch)

	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		controlID = self.windowControlID
		# ligne detat mise a jour toutes les secondes
		if controlID == 2 or objID == 1:
			return
		if controlID in [2, 3]:
			return

		printDebug("in event_valueChange InLessonWindow controlID %s, objID %s, role %s, value %s" % (controlID, objID, self.role, self.value))
		# affichage aide sur la touche avec  touche f2
		if controlID == 4 and objID in [2, 3, 4]\
			or controlID == 6 and objID == 2:
			StopTimer(GB_timer)
			GB_timer = wx.CallLater(300, SayValue, self.value.strip("\n\r"))

		elif controlID in [4]:
			pass
		# apres erreur, passsage automatique au caractere suivant
		elif controlID in [6]:
			objID = 5
		elif controlID == 9 and GB_precObjID == 5:
			DireInfosTemporisee(self, 300)
		elif controlID == 9 and objID == 4:
			DireInfosTemporisee(self, 300)

		elif controlID in [8, 9]:
			DireInfosTemporisee(self, 300)
		elif controlID in [7, 10]:
			if self.value is not None:
				DireInfosTemporisee(self, 300)
		elif controlID in [4, 5]:
			if (self.value is not None and len(self.value) > 0):
				DireInfosTemporisee(self, 100)
		GB_precObjID = objID
		printDebug("out event_valueChange InLessonWindow")

	def event_gainFocus(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("in event_gainFocus InLessonWindow controlID %s, objID %s, role  %s, value %s" % (controlID, objID, self.role, self.value))

		if controlID == 0:
			pass

		elif controlID in [7, 8, 9, 10]:
			StopTimer(GB_timer)
			DireInfosTemporisee(self, 200)

		else:
			SayValue(self.windowText)

		printDebug("out event_gainFocus InLesssonWindow")

	def GetInfos(self):
		try:
			oForeground = api.getForegroundObject().IAccessibleObject
			(o, childId) = accNavigate(oForeground, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			return
		if o.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo sans info")
			return ("", "", "", "", "")
		(o1, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		if o1.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo state invisible ")
			return ("", "", "", "", "")
		sATaper = o1.accValue(0)
		if sATaper is None:
			printDebug(" getInfo pas d'info a taper")
			return ("", "", "", "", "")
		sATaper = sATaper.strip(u" ")
		sATaper = sATaper.strip(u"\n\r")
		try:
			(o, childId) = accNavigate(o, 0, NAVDIR_PREVIOUS)
			(o2, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			printDebug("error 1, no object")
			return ("", "", "", "", "")
		sDejaTapee = o2.accValue(0)
		if sDejaTapee is None:
			printDebug(" getInfo deja taper introuvable")
			return ("", "", "", "", "")
		sDejaTapee = sDejaTapee.strip(u" ")
		sDejaTapee = sDejaTapee.strip(u"\n\r")
		sResteATaper = sATaper[len(sDejaTapee):]
		sMotCourant = ""
		if len(sATaper) <= 1:
			# pas de mot
			pass
		elif len(sDejaTapee) == 0:
			# mot courant = premier mot
			sMotCourant = sATaper.split(" ")[0]
		else:
			sMotCourant = sResteATaper.split(" ")[0]
		sCaractereCourant = ""
		if len(sResteATaper) > 0:
			sCaractereCourant = sResteATaper[0]
		return sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant

	def DireInfos(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		StopTimer(GB_timer)
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = self.GetInfos()
		printDebug("DireInfos ATaper %s, DejaTapee %s, ResteAtaper %s, Mot %s, Caractere %s" % (sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant))
		if sATaper == "":
			printDebug("direInfo sans info")
			return

		mode = getLessonMode(self, sATaper)
		#
		if mode == MODE_TOUCHE:
			SayText("", "", sATaper)

		elif mode == MODE_MOT:
			if objID == 5 and len(sDejaTapee) != 0:
				# erreur dire le caractere
				SayText("", "", sCaractereCourant)

			# dire le mot et le caractere si debut
			elif len(sDejaTapee) == 0:
				# plusieurs mot a taper?
				if len(sATaper.split(" ")) > 1:
					if sCaractereCourant == " ":
						sCaractereCourant = "espace"
					SayText(sATaper, sMotCourant, sCaractereCourant)
				else:
					SayText("", sMotCourant, sCaractereCourant)
			# ou si precede d'un espace
			elif sDejaTapee[-1] == " ":
				SayText("", sMotCourant, sCaractereCourant)

			else:
				SayText("",  "", sCaractereCourant)
		# dictee
		elif mode in [MODE_DICTEE_N1, MODE_DICTEE_N2]:
			# apres une erreur de frappe , dire le caractere a taper
			if objID == 5:
				SayText("", "", sCaractereCourant)
			# dire la prase et le mot si debut de frappe
			elif len(sDejaTapee) == 0:
				SayText("", sResteATaper, sMotCourant)
			elif sDejaTapee[-1] == "\n":
				SayText("", sResteATaper, sMotCourant)

			# dire si retour a la ligne
			elif sDejaTapee[-1] == "." and sCaractereCourant == "":
				speech.speakMessage("a la ligne")
		# on dit le mot que si premier caractere ou le caractere que si erreur
			elif sDejaTapee[-1] == " ":
				SayText("", "", sMotCourant)

			# apres erreur, changement de caractere

			elif (objID == 3 and GB_precObjID == 5):
				SayText("", "", sCaractereCourant)
			# dire les ponctuations
			elif sCaractereCourant in [".", ",", "!", ";", ":"]:
				SayText("", "", sCaractereCourant)
			elif mode in [MODE_DICTEE_N1]:
				# dire les espaces
				if len(sResteATaper) > 0 and sResteATaper[0] == " ":
					SayText("", "", "espace")
			else:
				pass
			return

		# par defaut, frappe lettre par lettre
		else:
			SayText("", "", sMotCourant)
		GB_precObjID = objID


class InLessonByKeyWindow(Window):
	def initOverlayClass(self):
		pass

	def event_typedCharacter(self, ch):
		printDebug("event_typedCharacter in InLessonByKeyWindow: ch = %s" % ch)
		StopTimer(GB_timer)
		return super(InLessonByKeyWindow, self).event_typedCharacter(ch)

	def _caretMovementScriptHelper(self, gesture, unit):
		gesture.send()

	def event_caret(self):
		pass

	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		controlID = self.windowControlID
		(scoreControlID, keyHelpControlID) = getScoreAndKeyHelpControlID(self)
		printDebug("in event_valueChange InLessonByKeyWindow controlID %s, objID %s , role %s, value %s" % (controlID, objID, self.role, self.value))
		# ne pas dire le timer
		if self.windowClassName == "ThunderRTTimer":
			pass

		# utiliser la mise à jour du score pour repeter la touche en cas d'erreur
		elif controlID == scoreControlID:
			DireInfosTemporisee(self, 200)
		# suite papui touche f2 pour avoir aide sur la touche
		elif controlID == keyHelpControlID:
			StopTimer(GB_timer)
			value = self.value.strip(u" ")
			SayValue(value.strip("\n\r"))
		elif controlID in [9]:
			DireInfosTemporisee(self, 200)
		printDebug("out event_valueChange InLessonByKeyWindow")

	def event_gainFocus(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("in event_gainFocus InLessonByKeyWindow controlID %s, objID %s, role  %s, value %s" % (controlID, objID, self.role, self.value))

		if controlID == 0:
			return
		printDebug("out event_gainFocus InLesssonByKeyWindow")

	def GetInfos(self):

		try:
			oForeground = GetTopLevelObject(self).children[3].IAccessibleObject
			(o, childId) = accNavigate(oForeground, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			return
		if o.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo sans info")
			return ("", "", "", "", "")
		(o1, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		if o1.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo state invisible ")
			return ("", "", "", "", "")
		sATaper = o1.accValue(0)
		if sATaper is None:
			printDebug(" getInfo pas d'info a taper")
			return ("", "", "", "", "")
		sATaper = sATaper.strip(u" ")
		sATaper = sATaper.strip(u"\n\r")
		try:
			(o, childId) = accNavigate(o, 0, NAVDIR_PREVIOUS)
			(o2, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			printDebug("error 1, no object")
			return ("", "", "", "", "")
		sDejaTapee = o2.accValue(0)
		if sDejaTapee is None:
			printDebug(" getInfo deja taper introuvable")
			return ("", "", "", "", "")
		sDejaTapee = sDejaTapee.strip(u" ")
		sDejaTapee = sDejaTapee.strip(u"\n\r")
		sResteATaper = sATaper[len(sDejaTapee):]
		sMotCourant = ""
		if len(sATaper) <= 1:
			# pas de mot
			pass
		elif len(sDejaTapee) == 0:
			# mot courant = premier mot
			sMotCourant = sATaper.split(" ")[0]
		else:
			sMotCourant = sResteATaper.split(" ")[0]
		sCaractereCourant = ""
		if len(sResteATaper) > 0:
			sCaractereCourant = sResteATaper[0]
		s = sMotCourant.split("-")
		s = " ".join(s)
		s = s.split("+")
		for i in s:
			if i.lower() == "y":
				s[s.index(i)] = "i grec"
		sMotCourant = " ".join(s)

		if len(sATaper) > 1:
			s = sATaper.split("-")
			s = " ".join(s)
			s = s.split("+")
		else:
			s = [sATaper, ]
		for i in s:
			if i.lower() == "y":
				s[s.index(i)] = "i grec"
		sATaper = " ".join(s)

		return sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant

	def DireInfos(self):
		global GB_timer, GB_precObjID
		# objID = GetObjectId(self)
		StopTimer(GB_timer)
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		printDebug("DireInfos ATaper %s, DejaTapee %s, ResteAtaper %s, Mot %s, Caractere %s" % (sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant))
		if sATaper == "":
			printDebug("direInfo sans info")
			return

		SayText("", "", sATaper)

	def DireLeCaractere(self):
		res = self.GetInfos()

		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if ("ESPACE" in sMotCourant[:6]) or (sCaractereCourant == " "):
			KeyboardInputGesture.fromName(" ").send()
			return
		if len(sMotCourant) > 1:
			SayText("", "", sMotCourant)
		else:
			SayText("", "", sCaractereCourant)


class InLessonByKeyWindow_1(InLessonByKeyWindow):
	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		controlID = self.windowControlID
		(scoreControlID, keyHelpControlID) = getScoreAndKeyHelpControlID(self)
		printDebug("in event_valueChange InLessonByKeyWindow_1 controlID %s, objID %s , role %s, value %s" % (controlID, objID, self.role, self.value))

		# utiliser la mise à jour du score pour repeter la touche en cas d'erreur
		if controlID == scoreControlID:
			DireInfosTemporisee(self, 300)
		# suite papui touche f2 pour avoir aide sur la touche
		elif controlID == keyHelpControlID:
			StopTimer(GB_timer)
			value = self.value.strip(u" ")
			GB_timer = wx.CallLater(200, SayValue, value.strip("\n\r"))
		elif controlID in [8, 9, 10]:
			DireInfosTemporisee(self, 200)
		printDebug("out event_valueChange InLessonByKeyWindow_1")


class InLessonByKeyWindow_2(InLessonByKeyWindow):
	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		controlID = self.windowControlID
		(scoreControlID, keyHelpControlID) = getScoreAndKeyHelpControlID(self)
		# utiliser la mise à jour du score pour repeter la touche en cas d'erreur
		if controlID == scoreControlID:
			pass
			return
		printDebug("in event_valueChange InLessonByKeyWindow_2 controlID %s, objID %s , role %s, value %s" % (controlID, objID, self.role, self.value))
		# suite papui touche f2 pour avoir aide sur la touche
		if controlID == keyHelpControlID:
			StopTimer(GB_timer)
			value = self.value.strip(u" ")
			GB_timer = wx.CallLater(200, SayValue, value.strip("\n\r"))
		elif controlID in [8, 9, 10]:
			DireInfosTemporisee(self, 300)
		printDebug("out event_valueChange InLessonByKeyWindow_2")


class InLessonByWordWindow(Window):
	def event_typedCharacter(self, ch):
		printDebug("event_typedCharacter in InLessonByWordWindow: ch = %s" % ch)
		StopTimer(GB_timer)
		return super(InLessonByWordWindow, self).event_typedCharacter(ch)

	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		controlID = self.windowControlID
		printDebug("in event_valueChange InLessonByWordWindow controlID %s, objID %s , role %s, value %s" % (controlID, objID, self.role, self.value))
		(aTaperControlID, dejaTapeControlID) = getATaperAndDejaTapeControlID()
		(scoreControlID, keyHelpControlID) = getScoreAndKeyHelpControlID(self)

		# ne pas dire le timer , ni le score
		if self.windowClassName == "ThunderRTTimer" or controlID == scoreControlID:
			pass
		# suite papui touche f2 pour avoir aide sur la touche
		elif controlID == keyHelpControlID:
			StopTimer(GB_timer)
			value = self.value.strip(u" ")
			GB_timer = wx.CallLater(200, SayValue, value)
		# dire l'info a taper
		elif controlID in [aTaperControlID, dejaTapeControlID]:
			DireInfosTemporisee(self, 200)
		printDebug("out event_valueChange InLessonByWordWindow")

	def event_gainFocus(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("in event_gainFocus InLessonByWordWindow controlID %s, objID %s, role  %s, value %s" % (controlID, objID, self.role, self.value))
		# SayValue(self.windowText)
		printDebug("out event_gainFocus InLessonByWordWindow")

	def getScoreControlID(self):
		# le score se trouve dans la premiere fenetre apres la fenetre de class ThunderRTPictureBox
		oDeb = api.getForegroundObject()
		for o in oDeb.children:
			if o.windowClassName == "ThunderRTPictureBox":
				return o.windowControlID + 1
		return -1

	def GetInfos(self):
		try:
			oForeground = api.getForegroundObject().IAccessibleObject
			(o, childId) = accNavigate(oForeground, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			return
		if o.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo sans info")
			return ("", "", "", "", "")
		(o1, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		if o1.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo state invisible ")
			return ("", "", "", "", "")
		sATaper = o1.accValue(0)
		if sATaper is None:
			printDebug(" getInfo pas d'info a taper")
			return ("", "", "", "", "")
		sATaper = sATaper.strip(u" ")
		sATaper = sATaper.strip(u"\n\r")
		try:
			(o, childId) = accNavigate(o, 0, NAVDIR_PREVIOUS)
			(o2, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			printDebug("error 1, no object")
			return ("", "", "", "", "")
		sDejaTapee = o2.accValue(0)
		if sDejaTapee is None:
			printDebug(" getInfo deja taper introuvable")
			return ("", "", "", "", "")
		sResteATaper = sATaper[len(sDejaTapee):]
		sMotCourant = ""
		if len(sATaper) <= 1:
			# pas de mot
			pass
		elif len(sDejaTapee) == 0:
			# mot courant = premier mot de sAtaper
			sMotCourant = sATaper.split(" ")[0]
		else:
			sMotCourant = sResteATaper.split(" ")[0]
		sCaractereCourant = ""
		if len(sResteATaper) > 0:
			sCaractereCourant = sResteATaper[0]
		return sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant

	def DireInfos(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		StopTimer(GB_timer)
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		printDebug("DireInfos ATaper %s, DejaTapee %s, ResteAtaper %s, Mot %s, Caractere %s" % (sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant))
		if sATaper == "":
			printDebug("direInfo sans info")
			return
		if objID == 5 and len(sDejaTapee) != 0:
			# erreur dire le caractere
			SayText("", "", sCaractereCourant)
		# dire le mot et le caractere si debut
		elif len(sDejaTapee) == 0:
			# plusieurs mot a taper?
			if len(sATaper.split(" ")) > 1:
				if sCaractereCourant == " ":
					sCaractereCourant = "espace"
				SayText(sATaper, sMotCourant, sCaractereCourant)

			else:
				SayText("", sMotCourant, sCaractereCourant)
		# ou si precede d'un espace
		elif sDejaTapee[-1] == " ":
			if len(sMotCourant) > 1:
				# mot avec plusierus caracteres, dire le mot et le caractere
				SayText("", sMotCourant, sCaractereCourant)
			else:
				# ne dire que le caractere
				SayText("", "", sCaractereCourant)
		else:
			SayText("", "", sCaractereCourant)

		GB_precObjID = objID

	def DireLeCaractere(self):
		global GB_timer
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if ("ESPACE" in sMotCourant) or (sCaractereCourant == " "):
			KeyboardInputGesture.fromName(" ").send()

			return
		if "A" <= sCaractereCourant and sCaractereCourant <= "Z":
			sCaractereCourant = sCaractereCourant.lower() + " majuscule"
		StopTimer()
		GB_timer = wx.CallLater(200, SayText, "", "", sCaractereCourant)

	def RepeterLeMot(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
			return

		if len(sMotCourant) != 0:
			speech.speakMessage(sMotCourant)
		elif len(sCaractereCourant) != 0:
			speech.speakMessage(sCaractereCourant)

	def EpelerLeMot(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
			return
		if len(sMotCourant) != 0:
			speech.speakMessage(sMotCourant)
			time.sleep(0.5)
			speech.speakSpelling(sMotCourant)
		elif len(sCaractereCourant) != 0:
			speech.speakMessage(sCaractereCourant)

	def DireLeReste(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
			return
		if len(sResteATaper) != 0:
			speech.speakMessage(sResteATaper)


class InLessonDictationWindow(Window):
	def event_typedCharacter(self, ch):
		printDebug("event_typedCharacter in InLessonDictationWindow: ch = %s" % ch)
		StopTimer(GB_timer)
		return super(InLessonDictationWindow, self).event_typedCharacter(ch)

	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		(aTaperControlID, dejaTapeControlID) = getATaperAndDejaTapeControlID()
		controlID = self.windowControlID
		(scoreControlID, keyHelpControlID) = getScoreAndKeyHelpControlID(self)
		# ne pas dire le timer, ni le scor
		if self.windowClassName == "ThunderRTTimer" or controlID == scoreControlID:
			return
		printDebug("in event_valueChange InLessonDictationWindow controlID %s, objID %s , role %s, value %s" % (controlID, objID, self.role, self.value))
		# suite papui touche f2 pour avoir aide sur la touche
		if controlID == keyHelpControlID:
			StopTimer(GB_timer)
			value = self.value.strip(u" ")
			GB_timer = wx.CallLater(200, SayValue, value)
		# utiliser la mise à jour du deja tapee pour dire la prochaine touche
		elif controlID in [aTaperControlID, dejaTapeControlID]:
			DireInfosTemporisee(self, 200)
		elif controlID in [8, ]:
			DireInfosTemporisee(self, 200)

		elif controlID in [9, ]:
			DireInfosTemporisee(self, 200)
		printDebug("out event_valueChange InLessonDictationWindow")

	def event_gainFocus(self):
		global GB_timer
		controlID = self.windowControlID
		objID = GetObjectId(self)
		printDebug("in event_gainFocus InLessonDictationWindow controlID %s, objID %s, role  %s, value %s" % (controlID, objID, self.role, self.value))
		# SayValue(self.windowText)
		printDebug("out event_gainFocus InLesssonDictationWindow")

	def GetInfos(self):
		try:
			oForeground = api.getForegroundObject().IAccessibleObject
			(o, childId) = accNavigate(oForeground, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			return
		if o.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo sans info")
			return ("", "", "", "", "")
		(o1, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		if o1.accState(0) & STATE_SYSTEM_INVISIBLE:
			printDebug("getInfo state invisible ")
			return ("", "", "", "", "")
		sATaper = o1.accValue(0)
		if sATaper is None:
			printDebug(" getInfo pas d'info a taper")
			GB_precObjID = objID
			return ("", "", "", "", "")
		sATaper = sATaper.strip(u" ")
		try:
			(o, childId) = accNavigate(o, 0, NAVDIR_PREVIOUS)
			(o2, childId) = accNavigate(o, 0, NAVDIR_LASTCHILD)
		except:  # noqa:E722
			printDebug("error 1, no object")
			return ("", "", "", "", "")
		sDejaTapee = o2.accValue(0)
		if sDejaTapee is None:
			printDebug(" getInfo deja taper introuvable")
			return ("", "", "", "", "")
		sResteATaper = sATaper[len(sDejaTapee):]
		sMotCourant = ""
		if len(sATaper) <= 1:
			# pas de mot
			pass
		elif len(sDejaTapee) == 0:
			# mot courant = premier mot de sAtaper
			sMotCourant = sATaper.split(" ")[0]
		else:
			sMotCourant = sResteATaper.split(" ")[0]
		sCaractereCourant = ""
		if len(sResteATaper) > 0:
			sCaractereCourant = sResteATaper[0]
		return sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant

	def DireInfos(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		# controlID = self.windowControlID
		StopTimer(GB_timer)
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		printDebug("DireInfos ATaper %s, DejaTapee %s, ResteAtaper %s, Mot %s, Caractere %s" % (sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant))
		if sATaper == "":
			printDebug("direInfo sans info")
			return
		# apres une erreur de frappe , dire le caractere a taper
		if objID == 5:
			SayText("", "", sCaractereCourant)				# dire la prase et le mot si debut de frappe
		elif len(sDejaTapee) == 0:
			if sATaper == sMotCourant:
				# dictee par mot, on ne dit que le mot
				SayText("", "", sMotCourant)
			else:
				SayText("", sResteATaper, sMotCourant)
		elif sDejaTapee[-1] == "\n":
			SayText("", sResteATaper, sMotCourant)

		# dire si retour a la ligne
		elif sDejaTapee[-1] == "." and sCaractereCourant == "":
			SayText("", "", "a la ligne")
		# on dit le mot que si premier caractere ou le caractere que si erreur
		elif sDejaTapee[-1] == " ":
			SayText("", "", sMotCourant)
		# apres erreur, changement de caractere
		elif (objID == 3 and GB_precObjID == 5):
			SayText("", "", sCaractereCourant)
		# dire les ponctuations
		elif sCaractereCourant in [".", ",", "!", ";", ":"]:
			SayText("", "", sCaractereCourant)
		GB_precObjID = objID

	def DireLeCaractere(self):
		global GB_timer
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if ("ESPACE" in sMotCourant) or (sCaractereCourant == " "):
			KeyboardInputGesture.fromName(" ").send()

			return
		if "A" <= sCaractereCourant and sCaractereCourant <= "Z":
			sCaractereCourant = sCaractereCourant.lower() + " majuscule"
		StopTimer()
		GB_timer = wx.CallLater(200, SayText, "", "", sCaractereCourant)

	def RepeterLeMot(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
		if len(sMotCourant) > 1:
			speech.speakMessage(sMotCourant)
		elif len(sMotCourant) == 1:
			SayText("", "", sCaractereCourant)

	def EpelerLeMot(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
			return
		if len(sMotCourant) > 1:
			speech.speakMessage(sMotCourant)
			time.sleep(0.5)
			speech.speakSpelling(sMotCourant)
		elif len(sMotCourant) == 1:
			# dire le caractere
			SayText("", "", sCaractereCourant)

	def DireLeReste(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
			return
		if len(sResteATaper) != 0:
			speech.speakMessage(sResteATaper)


class InLessonDictationWindow_1(InLessonDictationWindow):
	def event_valueChange(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		controlID = self.windowControlID
		# ne pas dire le timer
		if controlID in [1, 3]:
			return
		printDebug("in event_valueChange InLessonDictationWindow_1 controlID %s, objID %s , role %s, value %s" % (controlID, objID, self.role, self.value))
		# suite papui touche f2 pour avoir aide sur la touche
		if controlID == 5:
			StopTimer(GB_timer)
			value = self.value.strip(u" ")
			SayValue(value.strip("\n\r"))
		# on ne dit pas la prochaine touche
		elif controlID in [9, ]:
			pass

		elif controlID in [10, ]:
			DireInfosTemporisee(self, 200)
		printDebug("out event_valueChange InLessonDictationWindow_1")

	def DireInfos(self):
		global GB_timer, GB_precObjID
		objID = GetObjectId(self)
		# controlID = self.windowControlID
		StopTimer(GB_timer)
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		printDebug("DireInfos ATaper %s, DejaTapee %s, ResteAtaper %s, Mot %s, Caractere %s" % (sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant))
		if sATaper == "":
			printDebug("direInfo sans info")
			return
		# dire les espaces
		if len(sResteATaper) > 0 and sResteATaper[0] == " ":
			SayText("", "", "espace")
		elif len(sDejaTapee) == 0:
			if len(sATaper .split(" ")) == 1:
				# dictee par mot, on ne dit que le mot
				SayText("", "", sMotCourant)
			else:
				SayText("", sATaper, sMotCourant)
		elif sDejaTapee[-1] == "\n":
			SayText("", sResteATaper, sMotCourant)

		# dire si retour a la ligne
		elif sDejaTapee[-1] == "." and sCaractereCourant == "":
			SayText("", "", "a la ligne")
		# on dit le mot que si premier caractere ou le caractere que si erreur
		elif sDejaTapee[-1] == " ":
			SayText("", "", sMotCourant)
		# apres erreur, changement de caractere
		elif (objID == 3 and GB_precObjID == 5):
			SayText("", "", sCaractereCourant)
		# dire les ponctuations
		elif sCaractereCourant in [".", ", ", "!", ";", ":"]:
			SayText("", "", sCaractereCourant)

		GB_precObjID = objID

	def DireLeCaractere(self):
		global GB_timer
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if len(sCaractereCourant) != 0:
			if ("ESPACE" in sMotCourant) or (sCaractereCourant == " "):
				KeyboardInputGesture.fromName(" ").send()
				return
		SayText("", "", sCaractereCourant)

	def RepeterLeMot(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")
		if len(sMotCourant) != 0:
			ui.message(sMotCourant)

	def EpelerLeMot(self):
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = self.GetInfos()
		if sCaractereCourant == " ":
			speech.speakMessage("Vous devez appuyer sur la touche Espace")

		if len(sMotCourant) != 0:
			speech.speakMessage(sMotCourant)
			time.sleep(0.5)
			if len(sMotCourant) > 1 and len(sMotCourant) != len(sCaractereCourant):
				speech.speakSpelling(sMotCourant)

	def DireLeReste(self):
		res = self.GetInfos()
		if not res:
			return
		(sATaper, sDejaTapee, sResteATaper, sMotCourant, sCaractereCourant) = res
		if len(sResteATaper) != 0:
			if sCaractereCourant == " ":
				speech.speakMessage("Vous devez appuyer sur la touche Espace")
			else:
				SayText("", "", sATaper)


class AppModule(appModuleHandler.AppModule):
	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)

	def terminate(self):
		# restore use of NVDA keys
		self.restoreNVDAModifierKeys()
		super(AppModule, self).terminate()

	def saveNVDAModifierKeys(self):
		printDebug("save all NVDA modifier keys")
		self.useNumpadInsertAsNVDAModifierKey = config.conf["keyboard"]["useNumpadInsertAsNVDAModifierKey"]
		self.useExtendedInsertAsNVDAModifierKey = config.conf["keyboard"]["useExtendedInsertAsNVDAModifierKey"]
		self.useCapsLockAsNVDAModifierKey = config.conf["keyboard"]["useCapsLockAsNVDAModifierKey"]

	def event_appModule_gainFocus(self):
		global GB_moduleHasFocus
		printDebug("event_appModule_gainFocus")
		GB_moduleHasFocus = True
		from inputCore import manager
		numpadKeyNames = ["kb:numpad%s" % str(x) for x in range(1, 10)]
		numpadKeyNames .extend(["kb:numpadMultiply", "kb:numpadDivide", "kb:numpadPlus", ])
		d = {"globalCommands.GlobalCommands": {
			"None": numpadKeyNames}}
		self.localeGestureMap = manager.localeGestureMap._map.copy()
		manager.localeGestureMap.update(d)
		ac_voiceControl.initialize()
		# save all NVDA modifierKeys
		self.saveNVDAModifierKeys()

	def restoreNVDAModifierKeys(self):
		printDebug("restore all NVDA modifier Keys")
		if hasattr(self, "useNumpadInsertAsNVDAModifierKey"):
			config.conf["keyboard"]["useNumpadInsertAsNVDAModifierKey"] = self.useNumpadInsertAsNVDAModifierKey
		if hasattr(self, "useExtendedInsertAsNVDAModifierKey"):
			config.conf["keyboard"]["useExtendedInsertAsNVDAModifierKey"] = self.useExtendedInsertAsNVDAModifierKey
		if hasattr(self, "useCapsLockAsNVDAModifierKey"):
			config.conf["keyboard"]["useCapsLockAsNVDAModifierKey"] = self.useCapsLockAsNVDAModifierKey

	def event_appModule_loseFocus(self):
		global GB_moduleHasFocus
		printDebug("event_appModule_loseFocus")
		ac_voiceControl.terminate()
		GB_moduleHasFocus = False
		if hasattr(self, "localeGestureMap "):
			# restore localeGesture Map
			from inputCore import manager
			manager.localeGestureMap.clear()
			manager.localeGestureMap ._map = self.localeGestureMap .copy()
		# restore use of NVDA keys
		self.restoreNVDAModifierKeys()

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		global GB_moduleHasFocus, GB_inGetTopLevelFunction
		printDebug("choose overlayclass in,name= %s, controlID= %s, class= %s,role= %s" % (obj.name, obj.windowControlID, obj.windowClassName, obj.role))
		cls = "inchangee"
		if GB_inGetTopLevelFunction > 0:
			return
		if obj.windowClassName != u'ThunderRTTextBox':
			# printDebug("ChooseOverlayClass out %s, class= %s" % (cls , obj.windowClassName))
			return
		oTop = GetTopLevelObject(obj)
		if oTop is None:
			printDebug("erreur, pas de top object")
			return
		if obj.windowControlID == 8 and obj.role == 8:
			for c in [DisplayModelEditableText, EditableText, UnidentifiedEdit]:
				if c in clsList:
					clsList.remove(c)
		name = oTop.name
		if name is None:
			cls = "InOtherWindow"
			clsList.insert(0, InOtherWindow)
			for c in [DisplayModelEditableText, EditableText, UnidentifiedEdit]:
				if c in clsList:
					clsList.remove(c)
			printDebug("ChooseOverlayClass out %s, name: %s" % (cls, name))
			return
		if "Bienvenue" in name:
			cls = "InBienvenueWindow"
			clsList.insert(0, InBienvenueWindow)
			return
		if u"Aide-Mémoire" in name and "Menu" not in name:
			clsList.insert(0, InAideMemoireWindow)
			cls = "InAideMemoireWindow"
			return
		if u"Page" in name[:10]:
			clsList.insert(0, InPageWindow)
			cls = "InPageWindow"
			return
		for c in [DisplayModelEditableText, EditableText, UnidentifiedEdit]:
			if c in clsList:
				clsList.remove(c)
		if ((u"Leçon" in name and "Menu" not in name) or u"Exercice" in name):
			printDebug("controlID %s ,clsList %s" % (obj.windowControlID, clsList))
			sATaper = getATaperInfos()
			mode = getLessonMode(obj, sATaper)
			if mode == MODE_TOUCHE:
				cls = "InLessonByKeyWindow"
				clsList.insert(0, InLessonByKeyWindow)
				return
			if mode == MODE_TOUCHE_N1 or "Exercice" in name:
				cls = "InLessonByKeyWindow_1"
				clsList.insert(0, InLessonByKeyWindow_1)
				return
			if mode == MODE_TOUCHE_N2:
				cls = "InLessonByKeyWindow_2"
				clsList.insert(0, InLessonByKeyWindow_2)
				return
			if mode in [MODE_MOT]:
				cls = "InLessonByWordWindow"
				clsList.insert(0, InLessonByWordWindow)
				return
			if mode in [MODE_DICTEE_N1, MODE_DICTEE_N2]:
				cls = "InLessonDictationWindow"
				clsList.insert(0, InLessonDictationWindow)
				return
			if mode in [MODE_DICTEE_N3]:
				cls = "InLessonDictationWindow_1"
				clsList.insert(0, InLessonDictationWindow_1)
				return
			# par defaut,
			printDebug("lesson non repertoriee")
			cls = "InLessonWindow"
			clsList.insert(0, InLessonWindow)
			return
		else:
			cls = "InOtherWindow"
			clsList.insert(0, InOtherWindow)
		printDebug("ChooseOverlayClass out %s, name: %s" % (cls, name))

	def event_NVDAObject_init(self, obj):
		# printDebug("event_NVDAObject_init in:name= %s, role= %s" % (obj.name, obj.role))
		obj.objID = GetObjectId(obj)

	def event_foreground(self, obj, nextHandler):
		printDebug("event_foreground appModule:  name = \"%s\", childCount = %s" % (obj.name, obj.childCount))
		if not GB_moduleHasFocus:
			# comme on ne peut pas positionner le debit vocal pour les dictees
			# si dictee ou lesson on force le retour au menu principal
			name = obj.name
			if name is not None and (u"leçon" in name[:6].lower()):
				KeyboardInputGesture.fromName("Escape").send()
				time.sleep(0.5)
				api.processPendingEvents()
			return
		# positionne le debit vocal , les ponctuations et l'echo caractere suivant le titre et le contenu de la fenetre
		ac_voiceControl.updateSettings(obj)
		if obj.name is not None:
			name = obj.name.lower()
			# for lesson 16, desactivate numpad insert NVDA modifier key
			if name.startswith(u"leçon 16"):
				config.conf["keyboard"]["useNumpadInsertAsNVDAModifierKey"] = False
				printDebug("NVDA numpad insert key desactivated")
			# for lesson 12, deslactivate extended insert NVDA modifier key
			elif name.startswith(u"leçon 12"):
				config.conf["keyboard"]["useExtendedInsertAsNVDAModifierKey"] = False
				printDebug("NVDA Extended modifier key disabled")
			# for lesson 8a and c, desactivate capslock NVDA modifier key
			elif name.startswith(u"leçon 8 a") or name.startswith(u"leçon 8 c"):
				config.conf["keyboard"]["useCapsLockAsNVDAModifierKey"] = False
				printDebug("Capslock nvda modifier key disabled")
		else:
			# restore all NVDA modifier keys
			self.restoreNVDAModifierKeys()

	def event_gainFocus(selwf, obj, nextHandler):
		global GB_moduleHasFocus
		printDebug("in  event_gainfocus appModule: name= %s, role= %s" % (obj.name, obj.role))
		if not GB_moduleHasFocus:
			printDebug("out event_gainfocus appModule with no Focus")
			return
			# don't speak pane role when ThunderRTForm window has no name
		if obj.windowClassName == "ThunderRTForm" and obj.name is None and obj.childCount in [7, 9]:
			return
		nextHandler()
		printDebug("out event_gainfocus appModule")
		printDebug("out event_gainfocus appModule")

	def event_valueChange(self, obj, nextHandler):
		printDebug("in  event_valueChange appModule: name= %s, role= %s, value = %s" % (obj.name, obj.role, obj.value))
		nextHandler()

	def script_DireLeCaractere(self, gesture):
		obj = api.getFocusObject()
		if "DireLeCaractere" in dir(obj):
			obj.DireLeCaractere()
		else:
			gesture.send()

	def script_RepeterLeMot(self, gesture):
		printDebug("script RepeterLeMot")
		obj = api.getFocusObject()
		if "RepeterLeMot" in dir(obj):
			obj.RepeterLeMot()
		else:
			gesture.send()

	def script_EpelerLeMot(self, gesture):
		obj = api.getFocusObject()
		if "EpelerLeMot" in dir(obj):
			obj.EpelerLeMot()
		else:
			gesture.send()

	def script_DireLeReste(self, gesture):
		obj = api.getFocusObject()
		if "DireLeReste" in dir(obj):
			obj.DireLeReste()
		else:
			gesture.send()

	def script_TraceOnOff(self, gesture):
		global GB_traceMode
		if not GB_traceMode:
			GB_traceMode = True
			ui.message("Trace On")
		else:
			GB_traceMode = False
			ui.message("Trace Off")

	def script_test(self, gesture):
		print("ApprentiClavier test")
		ui.message("ApprentiClavier test")
		from .updateHandler.update_check import CheckForAddonUpdate
		fileName = os.path.join(globalVars.appArgs.configPath, "myAddons.latest")
		wx.CallAfter(CheckForAddonUpdate, None, updateInfosFile=fileName, silent=False, releaseToDev=True)

	__gestures = {
		"kb:nvda+control+f9": "TraceOnOff",
		"kb:nvda+shift+f9": "test",
		"kb:space": "DireLeCaractere",
		"kb:control+space": "RepeterLeMot",
		"kb:alt+space": "EpelerLeMot",
		"kb:shift+space": "DireLeReste"
		}
