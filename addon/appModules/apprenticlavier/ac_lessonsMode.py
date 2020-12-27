# appModules\apprenticlavier\ac_lessonsMode.py
# a part of apprentiClavierAccessEnhancement add-on
# Copyright (C) 2019-2020, Paulber19
# This file is covered by the GNU General Public License.


# constant for inLessonWindow class
MODE_INCONNU = 0
MODE_TOUCHE = 1
MODE_TOUCHE_N1 = 2
MODE_TOUCHE_N2 = 3
MODE_MOT = 4
MODE_DICTEE_N1 = 5
MODE_DICTEE_N2 = 6
MODE_DICTEE_N3 = 7
EXERCICES_LESSON_IDENTIFIER = ("99", "a")


lessonToMode = {
	"1": MODE_TOUCHE,
	"2a": MODE_TOUCHE_N1,
	"2b": MODE_TOUCHE_N1,
	"2c": MODE_TOUCHE_N1,
	"2d": MODE_MOT,
	"2e": MODE_TOUCHE_N1,
	"2f": MODE_MOT,
	"2g": MODE_MOT,
	"2h": MODE_MOT,
	"3a": MODE_TOUCHE_N1,
	"3b": MODE_TOUCHE_N1,
	"3c": MODE_MOT,
	"4": MODE_MOT,
	"5": MODE_MOT,
	"6": MODE_DICTEE_N3,
	"7": MODE_MOT,
	"8a": MODE_TOUCHE_N1,
	"8b": MODE_MOT,
	"8c": MODE_MOT,
	"8d": MODE_MOT,
	"8e": MODE_MOT,
	"8f": MODE_TOUCHE_N1,
	"8g": MODE_TOUCHE_N1,
	"8h": MODE_MOT,
	"9": MODE_MOT,
	"10": MODE_MOT,
	"11": MODE_DICTEE_N1,
	"12": MODE_TOUCHE,
	"13a": MODE_TOUCHE_N1,
	"13b": MODE_TOUCHE_N1,
	"13c": MODE_TOUCHE_N1,
	"13d": MODE_TOUCHE_N1,
	"13e": MODE_TOUCHE_N1,
	"13f": MODE_TOUCHE_N1,
	"13g": MODE_MOT,
	"14": MODE_DICTEE_N2,
	"15": MODE_DICTEE_N2,
	"16a": MODE_MOT,
	"16b": MODE_TOUCHE_N1,
	"16c": MODE_MOT,
	"16d": MODE_TOUCHE_N1,
	"17a": MODE_TOUCHE_N1,
	"17b": MODE_TOUCHE_N1,
	"17c": MODE_TOUCHE_N2,
	"17d": MODE_TOUCHE_N2,
	"18a": MODE_MOT,
	"18b": MODE_MOT,
	"18c": MODE_DICTEE_N2,
	"18d": MODE_DICTEE_N2,
	"18e": MODE_MOT,
	"19": MODE_DICTEE_N2
	}
