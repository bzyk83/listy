# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config, ConfigYesNo, ConfigSubsection
from enigma import eTimer
import urllib.request
import zipfile
import os
import glob
import datetime
import threading

config.plugins.bzyk83_downloader = ConfigSubsection()
config.plugins.bzyk83_downloader.autostart = ConfigYesNo(default=True)

PATH_ZIP = "/tmp/lista_kanalow.zip"
EXTRACT_PATH = "/etc/enigma2/"
LAST_UPDATE_FILE = "/etc/enigma2/.bzyk83_last_update"
AUTOSTART_CONFIG_FILE = "/etc/enigma2/.bzyk83_autostart"

# Bezpośrednie IP serwerów GitHub dla ominięcia blokad DNS w tunerze
URL_HB = "https://185.199.108"
URL_DUAL = "https://185.199.108"

def is_autostart_enabled():
    if os.path.exists(AUTOSTART_CONFIG_FILE):
        try:
            with open(AUTOSTART_CONFIG_FILE, "r") as f:
                return f.read().strip() == "1"
        except:
            pass
    return True

def set_autostart(state):
    try:
        with open(AUTOSTART_CONFIG_FILE, "w") as f:
            f.write("1" if state else "0")
    except:
        pass

def get_local_version():
    if os.path.exists(LAST_UPDATE_FILE):
        try:
            with open(LAST_UPDATE_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return "Brak danych"

def delete_old_bouquets():
    for pattern in ["userbouquet.*.tv", "userbouquet.*.radio"]:
        files = glob.glob(os.path.join(EXTRACT_PATH, pattern))
        for f in files:
            try:
                os.remove(f)
            except:
                pass

class DownloadListScreen(Screen):
    skin = """
    <screen position="center,center" size="600,240" title="Bzyk83 List Downloader">
        <widget name="status" position="10,20" size="580,60" font="Regular;20" halign="center" valign="center" />
        <widget name="info" position="10,90" size="580,30" font="Regular;16" halign="center" valign="center" fgColor="#aaaaaa" />
        <widget name="autostart_status" position="10,130" size="580,30" font="Regular;16" halign="center" valign="center" fgColor="#00ff00" />
        <widget name="key_red" position="10,190" size="130,40" backgroundColor="red" font="Regular;14" halign="center" valign="center" />
        <widget name="key_green" position="155,190" size="140,40" backgroundColor="green" font="Regular;14" halign="center" valign="center" />
        <widget name="key_yellow" position="305,190" size="140,40" backgroundColor="yellow" font="Regular;14" halign="center" valign="center" />
        <widget name="key_blue" position="455,190" size="135,40" backgroundColor="blue" font="Regular;14" halign="center" valign="center" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self["status"] = Label("Wtyczka gotowa. Wybierz wersję listy.")
        self["info"] = Label("Ostatnia aktualizacja: " + str(get_local_version()))
        self["autostart_status"] = Label("")
        
        self["key_red"] = Label("Wyjście")
        self["key_green"] = Label("Hotbird 13E")
        self["key_yellow"] = Label("Dual 13E+19E")
        self["key_blue"] = Label("Autostart")
        
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "red": self.close,
            "green": lambda: self.start_download_process("hb"),
            "yellow": lambda: self.start_download_process("dual"),
            "blue": self.toggle_autostart,
            "cancel": self.close
        }, -1)
        
        self.update_autostart_label()

    def update_autostart_label(self):
        if is_autostart_enabled():
            self["autostart_status"].setText("Auto-aktualizacja przy starcie: WŁĄCZONA")
        else:
            self["autostart_status"].setText("Auto-aktualizacja przy starcie: WYŁĄCZONA")

    def toggle_autostart(self):
        current_state = is_autostart_enabled()
        set_autostart(not current_state)
        self.update_autostart_label()

    def start_download_process(self, list_type):
        self["status"].setText("Pobieranie listy... Proszę czekać.")
        threading.Thread(target=self.worker, args=(list_type,)).start()

    def worker(self, list_type):
        try:
            url = URL_HB if list_type == "hb" else URL_DUAL
            
            if os.path.exists(PATH_ZIP):
                os.remove(PATH_ZIP)
                
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Host', '://githubusercontent.com')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(PATH_ZIP, "wb") as out_file:
                    out_file.write(response.read())
            
            if os.path.exists(PATH_ZIP) and os.path.getsize(PATH_ZIP) > 1024:
                self["status"].setText("Instalowanie nowej listy kanałów...")
                delete_old_bouquets()
                
                with zipfile.ZipFile(PATH_ZIP, 'r') as zip_ref:
                    zip_ref.extractall(EXTRACT_PATH)
                    
                os.remove(PATH_ZIP)
                
                today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                with open(LAST_UPDATE_FILE, "w") as f:
                    f.write(today_str)
                    
                os.system("wget -qO - http://127.0.0")
                self["status"].setText("Sukces! Lista została zaktualizowana.")
                self["info"].setText("Ostatnia aktualizacja: " + str(get_local_version()))
            else:
                self["status"].setText("Błąd: Plik ZIP z GitHub jest pusty.")
        except Exception as e:
            self["status"].setText("Błąd sieci: " + str(e)[:45])

def main(session, **kwargs):
    session.open(DownloadListScreen)

def silent_autostart_update():
    if not is_autostart_enabled():
        return
    try:
        req = urllib.request.Request(URL_DUAL)
        req.add_header('User-Agent', 'Mozilla/5.0')
        req.add_header('Host', '://githubusercontent.com')
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(PATH_ZIP, "wb") as out_file:
                out_file.write(response.read())
        if os.path.exists(PATH_ZIP) and os.path.getsize(PATH_ZIP) > 1024:
            delete_old_bouquets()
            with zipfile.ZipFile(PATH_ZIP, 'r') as zip_ref:
                zip_ref.extractall(EXTRACT_PATH)
            os.remove(PATH_ZIP)
            today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(LAST_UPDATE_FILE, "w") as f:
                f.write(today_str)
            os.system("wget -qO - http://127.0.0")
    except:
        pass

bzyk_timer = None

def timer_callback():
    threading.Thread(target=silent_autostart_update).start()

def autostart(reason, **kwargs):
    global bzyk_timer
    if reason == 0:
        bzyk_timer = eTimer()
        bzyk_timer.callback.append(timer_callback)
        bzyk_timer.start(25000, True)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Bzyk83 GitHub Downloader",
            description="Pobiera listy kanałów z automatycznym sprawdzaniem wersji i czyszczeniem",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_AUTOSTART,
            fnc=autostart
        )
    ]
