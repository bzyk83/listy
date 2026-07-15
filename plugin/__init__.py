# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import gettext

PluginLanguageDomain = "Bzyk83Downloader"
PluginLanguagePath = "Extensions/Bzyk83Downloader/locale"

def localeInit():
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def setTargetLanguage(language):
    gettext.textdomain(PluginLanguageDomain)

language.addCallback(setTargetLanguage)
localeInit()
