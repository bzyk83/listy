# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import gettext

PluginLanguageDomain = "Bzyk83Downloader"
PluginLanguagePath = "Extensions/Bzyk83Downloader/locale"

def localeInit():
    lang_path = resolveFilename(SCOPE_PLUGINS, PluginLanguagePath)
    gettext.bindtextdomain(PluginLanguageDomain, lang_path)

def setTargetLanguage(lang):
    gettext.textdomain(PluginLanguageDomain)

# Bezpieczna rejestracja callbacku dla Pythona 3
try:
    if setTargetLanguage not in language.listeners:
        language.listeners.append(setTargetLanguage)
except:
    language.addCallback(setTargetLanguage)

localeInit()
