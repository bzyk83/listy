# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config, ConfigYesNo, ConfigSubsection
from enigma import eTimer
import urllib.request
import ssl
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

# Bezpoœrednie linki do plików zip oraz plików wersji .version
URL_HB = "https://raw.githubusercontent.com/bzyk83/listy/main/hb.zip"
URL_DUAL = "https://raw.githubusercontent.com/bzyk83/listy/main/dual.zip"

URL_HB_VER = "https://raw.githubusercontent.com/bzyk83/listy/main/hb.version"
URL_DUAL_VER = "https://raw.githubusercontent.com/bzyk83/listy/main/dual.version"

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
    for pattern in ["userbouquet.*.tv", "userbouquet.*.radio", "bouquets.tv", "bouquets.radio"]:
        files = glob.glob(os.path.join(EXTRACT_PATH, pattern))
        for f in files:
            try:
                os.remove(f)
            except:
                pass

class DownloadListScreen(Screen):
    skin = """
    <screen position="center,center" size="1000,380" title="Bzyk83 List Downloader">
        <widget name="status" position="20,30" size="960,80" font="Regular;32" halign="center" valign="center" />
        <widget name="info" position="20,130" size="960,40" font="Regular;26" halign="center" valign="center" foregroundColor="#aaaaaa" />
        <widget name="autostart_status" position="20,190" size="960,40" font="Regular;26" halign="center" valign="center" foregroundColor="#00ff00" />
        <widget name="key_red" position="20,290" size="220,60" backgroundColor="red" font="Regular;22" halign="center" valign="center" />
        <widget name="key_green" position="265,290" size="230,60" backgroundColor="green" font="Regular;22" halign="center" valign="center" />
        <widget name="key_yellow" position="515,290" size="230,60" backgroundColor="yellow" font="Regular;22" halign="center" valign="center" />
        <widget name="key_blue" position="765,290" size="215,60" backgroundColor="blue" font="Regular;22" halign="center" valign="center" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self["status"] = Label("Wtyczka gotowa. Wybierz wersjê listy.")
        self["info"] = Label("Ostatnia aktualizacja: " + str(get_local_version()))
        self["autostart_status"] = Label("")
        
        self["key_red"] = Label("Wyjœcie")
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
        
        self.gui_timer = eTimer()
        
        try:
            self.gui_timer_conn = self.gui_timer.timeout.connect(self.update_gui_status)
        except AttributeError:
            self.gui_timer.callback.append(self.update_gui_status)
            self.gui_timer_conn = None
            
        self.status_message = ""
        self.info_message = ""
        
        self.update_autostart_label()

    def update_autostart_label(self):
        if is_autostart_enabled():
            self["autostart_status"].setText("Auto-aktualizacja przy starcie: W£¥CZONA")
        else:
            self["autostart_status"].setText("Auto-aktualizacja przy starcie: WY£¥CZONA")

    def toggle_autostart(self):
        current_state = is_autostart_enabled()
        set_autostart(not current_state)
        self.update_autostart_label()

    def trigger_gui_update(self, status_text, info_text=None):
        self.status_message = status_text
        if info_text is not None:
            self.info_message = info_text
        self.gui_timer.start(50, True)

    def update_gui_status(self):
        self["status"].setText(self.status_message)
        if self.info_message:
            self["info"].setText(self.info_message)

    def start_download_process(self, list_type):
        self["status"].setText("Sprawdzanie wersji na serwerze...")
        threading.Thread(target=self.worker, args=(list_type,)).start()

    def worker(self, list_type):
        try:
            url_zip = URL_HB if list_type == "hb" else URL_DUAL
            url_ver = URL_HB_VER if list_type == "hb" else URL_DUAL_VER
            
            context = ssl._create_unverified_context()
            
            # 1. Pobranie wersji z GitHuba
            remote_version = "Nieznana"
            try:
                req_ver = urllib.request.Request(url_ver)
                req_ver.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
                with urllib.request.urlopen(req_ver, context=context, timeout=8) as response:
                    remote_version = response.read().decode('utf-8').strip()
            except Exception as e:
                # Jeœli plik wersji nie istnieje, kontynuujemy bez sprawdzania
                pass

            local_version = get_local_version()
            
            if remote_version != "Nieznana" and local_version == remote_version:
                self.trigger_gui_update("Masz ju¿ najnowsz¹ wersjê listy!", "Wersja na dekoderze: " + local_version)
                # Dajemy 3 sekundy na przeczytanie komunikatu zanim pozwolimy pobraæ ponownie na si³ê
                import time
                time.sleep(3)
                
            self.trigger_gui_update("Pobieranie paczki z GitHub...")
            
            if os.path.exists(PATH_ZIP):
                try:
                    os.remove(PATH_ZIP)
                except:
                    pass
                
            req = urllib.request.Request(url_zip)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            
            with urllib.request.urlopen(req, context=context, timeout=15) as response:
                with open(PATH_ZIP, "wb") as out_file:
                    out_file.write(response.read())
            
            if os.path.exists(PATH_ZIP) and os.path.getsize(PATH_ZIP) > 1024:
                self.trigger_gui_update("Instalowanie nowej listy kana³ów...")
                delete_old_bouquets()
                
                with zipfile.ZipFile(PATH_ZIP, 'r') as zip_ref:
                    zip_ref.extractall(EXTRACT_PATH)
                    
                try:
                    os.remove(PATH_ZIP)
                except:
                    pass
                
                # Zapisujemy now¹ wersjê pobran¹ z pliku .version (lub bie¿¹cy czas, jeœli plik by³ pusty)
                version_to_save = remote_version if remote_version != "Nieznana" else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                with open(LAST_UPDATE_FILE, "w") as f:
                    f.write(version_to_save)
                    
                os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=4")
                self.trigger_gui_update("Sukces! Lista zosta³a zaktualizowana.", "Ostatnia aktualizacja: " + version_to_save)
            else:
                self.trigger_gui_update("B³¹d: Plik ZIP z GitHub jest uszkodzony lub pusty.")
        except Exception as e:
            self.trigger_gui_update("B³¹d sieci: " + str(e)[:45])

def main(session, **kwargs):
    session.open(DownloadListScreen)

def silent_autostart_update():
    if not is_autostart_enabled():
        return
    try:
        context = ssl._create_unverified_context()
        
        # 1. SprawdŸ wersjê przed cichym pobraniem
        remote_version = "Nieznana"
        try:
            req_ver = urllib.request.Request(URL_DUAL_VER)
            req_ver.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            with urllib.request.urlopen(req_ver, context=context, timeout=8) as response:
                remote_version = response.read().decode('utf-8').strip()
        except:
            pass
            
        local_version = get_local_version()
        
        # Jeœli wersje s¹ identyczne, nie obci¹¿amy niepotrzebnie tunera
        if remote_version != "Nieznana" and local_version == remote_version:
            return
            
        req = urllib.request.Request(URL_DUAL)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        with urllib.request.urlopen(req, context=context, timeout=15) as response:
            with open(PATH_ZIP, "wb") as out_file:
                out_file.write(response.read())
        if os.path.exists(PATH_ZIP) and os.path.getsize(PATH_ZIP) > 1024:
            delete_old_bouquets()
            with zipfile.ZipFile(PATH_ZIP, 'r') as zip_ref:
                zip_ref.extractall(EXTRACT_PATH)
            try:
                os.remove(PATH_ZIP)
            except:
                pass
            
            version_to_save = remote_version if remote_version != "Nieznana" else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(LAST_UPDATE_FILE, "w") as f:
                f.write(version_to_save)
            os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=4")
    except:
        pass

bzyk_timer = None

def timer_callback():
    threading.Thread(target=silent_autostart_update).start()

def autostart(reason, **kwargs):
    global bzyk_timer
    if reason == 0:
        bzyk_timer = eTimer()
        try:
            bzyk_timer_conn = bzyk_timer.timeout.connect(timer_callback)
        except AttributeError:
            bzyk_timer.callback.append(timer_callback)
        bzyk_timer.start(25000, True)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Bzyk83 GitHub Downloader",
            description="Pobiera listy kana³ów z automatycznym sprawdzaniem wersji i czyszczeniem",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_AUTOSTART,
            fnc=autostart
        )
