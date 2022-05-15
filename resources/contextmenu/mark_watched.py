# -*- coding: utf-8 -*-
import sys
from xbmc import executebuiltin, sleep

executebuiltin("RunPlugin(%s)" % sys.listitem.getProperty('B99_watched_params'))
sleep(1000)
executebuiltin('UpdateLibrary(video,special://skin/foo)')
