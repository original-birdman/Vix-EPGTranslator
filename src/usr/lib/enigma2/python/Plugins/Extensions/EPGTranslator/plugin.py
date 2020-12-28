# -*- coding: utf-8 -*-
#
from __future__ import print_function

EPGTrans_vers = "2.0"

from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigSubsection, ConfigSelection, ConfigInteger, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from enigma import eEPGCache, eServiceReference, getDesktop
from Plugins.Plugin import PluginDescriptor
from Screens.EpgSelection import EPGSelection
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists

from twisted.web.client import getPage

import socket, sys, re, time

# Imports and defs which are version-dependent
#
if sys.version_info[0] == 2:
# python2 version
    from urllib import quote
    from urllib2 import Request, urlopen, URLError, HTTPError
    def dec2utf8(n):         return unichr(n).encode('utf-8')

else:
# python3 version
    from urllib.parse import quote
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
# No unichr in Py3. chr() returns a unicode string.
#
    def dec2utf8(n):         return chr(n)

# Useful constants for EPG fetching.
#
#   B = Event Begin Time
#   D = Event Duration
#   T = Event Title
#   S = Event Short Description
#   E = Event Extended Description
#   I = Event Id
#   N = Service Name

EPG_OPTIONS = 'BDTSEINX'    # X MUST be last to keep index correct!!!

# Now split this into mnemonic indices.
# Then we can use epg_T etc... and means that any change to EPG_OPTIONS
# is automatically handled
#
for i in range(len(EPG_OPTIONS)):
    exec("epg_%s = %d" % (EPG_OPTIONS[i], i))

# Translate HTML Entities (&xxx;) in text
# The standard python name2codepoint (in htmlentitydefs for py2,
# html.entities for py3) is incomplete, so we'll use a complete
# one (which is easy to create).
#
def transHTMLEnts(text):
    from .HTML5Entities import name2codepoint
    def repl(ent):
        res = ent.group(0)      # get the text of the match
        ent = res[1:-1].lower() # Strip & and ;
        if re.match("#\d+", ent):  # Numeric entity
            res = dec2utf8(int(ent[1:]))
        else:
            try:                    # Look it up...
                res = dec2utf8(name2codepoint[ent])
            except:                 # Leave as-is
                pass
        return res

    text = re.sub("&.{,30}?;", repl, text)

    return str(text)

# The routine to actually translate the text.
# This is not an object method, so that it can be called from "anywhere"
#
dflt_UA = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0'

# This routine expects to get normal ("raw") text and will return the
# same.
# So it knows about URL encoding and HTMLEntity translation, so that the
# callers do not need to.
#
def DO_translation(text, source, dest):
# We need to url-encode the text (so "quote" is a misnamed function).
#
    text = quote(text)
# The /m url produces a smaller result to the "full" (/) page.
# It also (more importantly) actually returns the translated text!
#
    url = 'https://translate.google.com/m?&sl=%s&tl=%s&q=%s' % (source, dest, text)
    agents = {'User-Agent': dflt_UA}
# We'll extract the result from the returned web-page
# This is currently (07 Dec 2020) in a div with its last item making it
# a result-container...
#
    before_trans = 'class="result-container">'
    request = Request(url, headers=agents)
    try:
# Ensure the result is marked as utf-8 (Py2 needs it, Py3 doesn't, but
# doesn't object to the usage).
#
        output = urlopen(request, timeout=20).read().decode('utf-8')
        data = output[output.find(before_trans) + len(before_trans):]
# ...and we want everything up to the end of the div
#
        newtext = data.split('</div>')[0]
        newtext = transHTMLEnts(newtext)
    except URLError as e:
        newtext = 'URL Error: ' + str(e.reason)
    except HTTPError as e:
        newtext = 'HTTP Error: ' + str(e.code)
    except socket.error as e:
        newtext = 'Socket Error: ' + str(e)
    return newtext

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
# Our classes
#
# The list of available languages
#
langs =  [
 ('af', _('Afrikaans')),
 ('sq', _('Albanian')),
 ('ar', _('Arabic')),
 ('az', _('Azerbaijani')),
 ('eu', _('Basque')),
 ('be', _('Belarusian')),
 ('bs', _('Bosnian')),
 ('bg', _('Bulgarian')),
 ('ca', _('Catalan')),
 ('ceb', _('Cebuano')),
 ('hr', _('Croatian')),
 ('cs', _('Czech')),
 ('da', _('Danish')),
 ('nl', _('Dutch')),
 ('en', _('English')),
 ('et', _('Estonian')),
 ('tl', _('Filipino')),
 ('fi', _('Finnish')),
 ('fr', _('French')),
 ('gl', _('Galician')),
 ('de', _('German')),
 ('el', _('Greek')),
 ('ht', _('Haitian Creole')),
 ('hu', _('Hungarian')),
 ('is', _('Icelandic')),
 ('id', _('Indonesian')),
 ('ga', _('Irish')),
 ('it', _('Italian')),
 ('jw', _('Javanese')),
 ('lv', _('Latvian')),
 ('lt', _('Lithuanian')),
 ('mk', _('Macedonian')),
 ('ms', _('Malay')),
 ('mt', _('Maltese')),
 ('no', _('Norwegian')),
 ('fa', _('Persian')),
 ('pl', _('Polish')),
 ('pt', _('Portuguese')),
 ('ro', _('Romanian')),
 ('ru', _('Russian')),
 ('sr', _('Serbian')),
 ('sk', _('Slovak')),
 ('sl', _('Slovenian')),
 ('es', _('Spanish')),
 ('sw', _('Swahili')),
 ('sv', _('Swedish')),
 ('tr', _('Turkish')),
 ('uk', _('Ukrainian')),
 ('ur', _('Urdu')),
 ('vi', _('Vietnamese')),
 ('cy', _('Welsh'))
]

# Source has an auto option in first place on the list
#
config.plugins.translator = ConfigSubsection()
config.plugins.translator.source = ConfigSelection(default='auto',
 choices=[ ( 'auto', _('Detect Language')) ] + langs[:] )

# Destination has no auto...
#
config.plugins.translator.destination = ConfigSelection(default='en',
 choices=langs)
config.plugins.translator.maxevents = ConfigInteger(20, (2, 999))
config.plugins.translator.showsource = ConfigSelection(default='yes',
 choices=[('yes', _('Yes')), ('no', _('No'))])

# Interpolate dynamic values using {xxx}.
# Used for skins, where time formats may contain %H:%M etc...,
# making % replacements a bit messy
#
def applySkinVars(skin, dict):
    for key in list(dict.keys()):   # Py3 needs the list, Py2 is OK with it
        try:
            skin = skin.replace('{' + key + '}', dict[key])
        except Exception as e:
            print(e, '@key=', key)
    return skin

# Get the skin settings etc. that are dependent on screen size.
# If the screen size isn't (always a) constant between Vix start-ups
# then this call will need to go into the __init__ defs of each class
# that needs to use MySD instead, and save that to (and use) self.MySD.
#
if getDesktop(0).size().width() <= 1280:
    exec("from .Skin_small import MySD")
else:
    exec("from .Skin_medium import MySD")

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
#
class translatorConfig(ConfigListScreen, Screen):

    def __init__(self, session):
        self.skin = MySD.translatorConfig_skin
        Screen.__init__(self, session)
        self['flag'] = Pixmap()
        list = []
        list.append(getConfigListEntry(_('Source Language:'), config.plugins.translator.source))
        list.append(getConfigListEntry(_('Destination Language:'), config.plugins.translator.destination))
        list.append(getConfigListEntry(_('Maximum EPG Events:'), config.plugins.translator.maxevents))
        list.append(getConfigListEntry(_('Show Source EPG:'), config.plugins.translator.showsource))

        ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.save,
         'cancel': self.cancel,
         'red': self.cancel,
         'green': self.save}, -1)
        self.onLayoutFinish.append(self.UpdateComponents)

    def UpdateComponents(self):
        png = '/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/flag/' + str(config.plugins.translator.destination.value) + '.png'
        if fileExists(png):
            self['flag'].instance.setPixmapFromFile(png)
        current = self['config'].getCurrent()

    def save(self):
        for x in self['config'].list:
            x[1].save()
            configfile.save()

        self.exit()

    def cancel(self):
        for x in self['config'].list:
            x[1].cancel()

        self.exit()

    def exit(self):
        self.session.openWithCallback(self.close, translatorMain, None)
        return

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
#
class translatorMain(Screen):

# Create the helptext as a class variable
# This will be used as the basis for translations into other
# destination languages and the result will be kept for re-use
#
    helptext = {}
    base_helptext = """
Inside Plugin:
Left <-> Right : <-> +- EPG Event
Ok : translate Text
Bouquet : +- Zap
Menu : Setup
"""

    def __init__(self, session, text):
        self.showsource = config.plugins.translator.showsource.value

        if self.showsource == 'yes':    size = MySD.tMyes
        else:                           size = MySD.tMno

        self.dict = {'size': size}
        self.skin = applySkinVars(MySD.translatorMain_skin, self.dict)
        self.session = session
        Screen.__init__(self, session)

        self.source = str(config.plugins.translator.source.value)
        self.destination = str(config.plugins.translator.destination.value)
        self.text = text
        self.hideflag = True
        self.refresh = False
        self.max = 1
        self.count = 0
        self.list = []
        self.translations = {}
        self.eventName = ''
        self['flag'] = Pixmap()
        self['flag2'] = Pixmap()
        self['text'] = ScrollLabel('')
        self['text2'] = ScrollLabel('')
        self['label'] = Label('= Hide')
# MovieSelectionActions are there so that Menu and Info keys work!(?)
        self['actions'] = ActionMap(['OkCancelActions',
         'DirectionActions',
         'ChannelSelectBaseActions',
         'ColorActions',
         'MovieSelectionActions',
         'HelpActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'nextBouquet': self.zapDown,
         'prevBouquet': self.zapUp,
         'red': self.getEPG,
         'green': self.showHelp,
         'blue': self.hideScreen,
         'contextMenu': self.config,
         'bluelong': self.showHelp,
         'showEventInfo': self.showHelp}, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)

# Add the English (base) helptext if it is not there.
# This ensures it gets added with the same newline spacing as any other
# language
        if 'en' not in self.helptext:
            self.helptext['en'] = self.get_translation(self.base_helptext, from_lg='en', to_lg='en')

# Add the helptext for the environment language and default destination
# now
        for lang in (language.getLanguage()[:2], self.destination):
            if lang not in self.helptext:
                self.helptext[lang] = self.get_translation(self.helptext['en'], from_lg='en', to_lg=lang)

    def onLayoutFinished(self):
        source = '/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/flag/' + self.source + '.png'
        destination = '/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/flag/' + self.destination + '.png'
        if self.showsource == 'yes':
            if fileExists(source):
                self['flag'].instance.setPixmapFromFile(source)
            if fileExists(destination):
                self['flag2'].instance.setPixmapFromFile(destination)
        elif fileExists(destination):
            self['flag'].instance.setPixmapFromFile(destination)
        if self.text is None:   self.getEPG()
        else:                   self.translateEPG(self.text)
        return

    def ok(self):
        self.session.openWithCallback(self.translateText, VirtualKeyBoard, title='Text Translator:', text='')

# Routine to get the actual translation of the given text
# We are allowed to force the source or destination language...
#
    def get_translation(self, text, from_lg=None, to_lg=None):
        if len(text) > 2000:
            text = text[0:2000]
        if from_lg != None: source = from_lg
        else:               source = self.source
        if to_lg != None:   dest = to_lg
        else:               dest = self.destination
        return DO_translation(text, source, dest)

# Translate the text (entered via a VirtualKeyboard)
# and display it
#
    def translateText(self, text):
        if not text or text == '':      # Don't do nothing
            return
        self.setTitle('Text Translator')
        newtext = self.get_translation(text)
        if self.showsource == 'yes':
            self['text'].setText(text)
            self['text2'].setText(newtext)
        else:
            self['text'].setText(newtext)
            self['text2'].hide()

# Translate the text of an EPG description
# and display it
#
    def translateEPG(self, text, do_translate=True):
        if not text or text == '':      # Don't do nothing
            return
        self.setTitle('EPG Translator')
        try:
            begin=time.strftime('%Y-%m-%d %H:%M', time.localtime(int(self.event[epg_B])))
            duration = "%d min" % (int(self.event[epg_D]) / 60)
        except:
            begin = ''
            duration = ''
        if do_translate:
            newtext = self.get_translation(text)
            try:
                uref = str(self.event[epg_I]) + ":" + self.event[epg_N]
                self.translations[uref] = newtext
            except:
                pass
        else:
            newtext = text
        newtext = re.sub('\n ', '\n', newtext)
        if self.refresh == False:
            newtext = begin + '\n\n' + newtext + '\n\n' + duration
            newtext = re.sub('\n\n\n\n', '\n\n', newtext)
        if self.showsource == 'yes':
            if self.refresh == False:
                self['text'].setText(begin + '\n\n' + text + '\n\n' + duration)
            else:
                self['text'].setText(text)
            self['text2'].setText(newtext)
        else:
            self['text'].setText(newtext)
            self['text2'].hide()

# Populate the EPG data in self.list from the box's EPG cache
#
    def getEPG(self):
        self.max = 1
        self.count = 0
        self.list = []
        service = self.session.nav.getCurrentService()
        info = service.info()
        curEvent = info.getEvent(0)
        if curEvent:
# We'll get the same EPG as would be displayed - so we start at
# config.epg.histminutes before now
# Do we actually need to limit the entry count at all???
# Could we just remember everything we get?
#
            t_now = int(time.time())
            epg_base = t_now - 60*int(config.epg.histminutes.value)
            epg_extent = 86400*14   # 14 days later
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            test = [ EPG_OPTIONS, (ref.toString(), 0, epg_base, epg_extent) ]
            epgcache = eEPGCache.getInstance()
            epg_data = epgcache.lookupEvent(test)
# Copy over only up to the maximum requested...
# returned list items (see lib/dvb/epgcache.cpp).
#
            self.list = epg_data[:int(config.plugins.translator.maxevents.value)]
            self.max = len(self.list)
# Set the starting point to the currently running service, which will be
# the last one before one with a future starting time
#
            self.count = 0      # In case we don't find one...
            for i in range(1,len(self.list)):
                if self.list[i][epg_B] > t_now: break
                self.count = i
        self.showEPG()
        return

# Get the (translated) EPG text to show
#
    def showEPG(self):
        try:
            self.event = self.list[self.count]
# If we already have the translation, just use it.
#
            uref = str(self.event[epg_I]) + ":" + self.event[epg_N]
            if uref in self.translations:
                self.translateEPG(str(self.translations[uref]), do_translate=False)
                self.refresh = False
                return
            text=self.event[epg_T]
            short=self.event[epg_S]
            ext=self.event[epg_E]
            self.refresh = False
        except:
            text = 'Press red button to refresh EPG'
            short = ''
            ext = ''
            self.refresh = True
        if short and short != text:
            text += '\n\n' + short
        if ext:
            if text:
                text += '\n\n'
            text += ext
        self.translateEPG(str(text))

    def leftUp(self):
        self.count -= 1
# Don't wrap....
        if self.count == -1:
            self.count = 0
        self.showEPG()

    def rightDown(self):
        self.count += 1
# Don't wrap....
        if self.count == self.max:
            self.count = self.max - 1
        self.showEPG()

    def up(self):
        self['text'].pageUp()
        self['text2'].pageUp()

    def down(self):
        self['text'].pageDown()
        self['text2'].pageDown()

    def zapUp(self):
        if InfoBar and InfoBar.instance:
            InfoBar.zapUp(InfoBar.instance)
            self.getEPG()

    def zapDown(self):
        if InfoBar and InfoBar.instance:
            InfoBar.zapDown(InfoBar.instance)
            self.getEPG()

    def showHelp(self):
# Display the help in the current environment and destination language
# (but only show once if these are the same text)
# Use our translation code to get this from the English
#
        env_lang = language.getLanguage()[:2]
        for lang in (env_lang, self.destination):
            if lang not in self.helptext:
                self.helptext[lang] = self.get_translation(self.helptext['en'], from_lg='en', to_lg=lang)
        text = "EPG Translator version: " + EPGTrans_vers
        text += "\n\n" + self.helptext[env_lang]
        if self.helptext[env_lang] != self.helptext[self.destination]:
            text += "\n\n" + self.helptext[self.destination]
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO, close_on_any_key=True)

    def config(self):
        self.session.openWithCallback(self.exit, translatorConfig)

    def hideScreen(self):
        with open('/proc/stb/video/alpha', 'w') as f:
            count = 40
            while count >= 0:
                if self.hideflag:   wv = count      # 40 -> 0
                else:               wv = 40 - count # 0 -> 40
                f.write('%i' % (config.av.osd_alpha.value * wv / 40))
                f.flush()               # So it does something
                count -= 1
        self.hideflag = not self.hideflag

    def exit(self):
        if self.hideflag == False:
            with open('/proc/stb/video/alpha', 'w') as f:
                f.write('%i' % config.av.osd_alpha.value)
        self.close()

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
# Code to link into EventView windows to allow thme to be translated by
# pressing the Text key.
#
from Screens.EventView import EventViewBase

orig_EVB__init__ = None
orig_EVB_setEvent = None
orig_EPGSel__init__ = None

# Start-up link (see PluginDescriptor defs)
# This gets the current EventViewBase.__init__, saves it (so it can
# still be called) and replaces it with my "added-handler".
#
def autostart(reason, **kwargs):
    global orig_EVB__init__, orig_EVB_setEvent, orig_EPGSel__init__
    orig_EVB__init__ = EventViewBase.__init__
    EventViewBase.__init__ = My_EVB__init__
    orig_EPGSel__init__ = EPGSelection.__init__
    try:
        check = EPGSelection.setPiPService
        EPGSelection.__init__ = My_EPGSelVTi__init__
    except AttributeError:
        try:
            check = EPGSelection.togglePIG
            EPGSelection.__init__ = My_EPGSelATV__init__
        except AttributeError:
            try:
                check = EPGSelection.runPlugin
                EPGSelection.__init__ = My_EPGSelPLI__init__
            except AttributeError:
                EPGSelection.__init__ = My_EPGSel__init__

# Code to toggle whether we are translating.
# Bound to Text in any EventView screen.
#
EPG_translating = False
EPG_lastevent = None

def EPG_ToggleMode():
    global EPG_translating
    EPG_translating = not EPG_translating
# We need to update the event text - its translation state has changed.
#
    My_setEvent(EPG_lastevent)

# The code to handle the text that will be displayed.
# This is an extention of the EventViewbase.setEvent().
#
orig_setEvent = None

def My_setEvent(event):
    global orig_setEvent, EPG_lastevent

# First, call the original code
#
    orig_setEvent(event)

# Remember this event, so that EPG_ToggleMode() can call us again with
# the same event info after a Text press.
#
    EPG_lastevent = event
    if EPG_translating:

# If we are now translating we need to change the text which the
# orig_setEvent() call above has set.
# We duplicate the login from the end of EventViewbase.setEvent() to get
# the new texts to set.
#
        text = event.getEventName()
        short = event.getShortDescription()
        extended = event.getExtendedDescription()

        if short == text:
            short = ""
        if short and extended:
            extended = short + '\n' + extended
        elif short:
            extended = short
# Need to cache the result and re-use it if we have it...
#
        newtext = DO_translation(extended,
            str(config.plugins.translator.source.value),
            str(config.plugins.translator.destination.value)
        )
        EVB_inst["FullDescription"].setText(newtext)
        EVB_inst["summary_description"].setText(newtext)

# The code to add my extensions to EventViewBase.__init__()
#
EVB_inst = None

def My_EVB__init__(self, Event, Ref, callback = None, similarEPGCB = None):
    global EVB_inst, EPG_translating
    global orig_EVB__init__, orig_setEvent

# First, call the original code, and remember the instance that called
# here.
#
    orig_EVB__init__(self, Event, Ref, callback, similarEPGCB)
    EVB_inst = self

# Add the bits to get a Text key handler for EventViewBase
# We create our own ActionMap. The VirtualKeyboardActions contexts only
# defines a Text key (convenient!) and calls it "showVirtualKeyboard".
#
    which= "EPGTrans"
    self[which] = ActionMap(["VirtualKeyboardActions"],
           {"showVirtualKeyboard": EPG_ToggleMode}, -1)
    self[which].setEnabled(True)
# Now set us to not-translting, trap the setEvent() from self and
# install my own handler
#
    EPG_translating = False
    orig_setEvent = self.setEvent
    self.setEvent = My_setEvent


def My_EPGSel__init__(self, session, service, zapFunc = None, eventid = None, bouquetChangeCB = None, serviceChangeCB = None):
    orig_EPGSel__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)

def My_EPGSelVTi__init__(self, session, service, zapFunc = None, eventid = None, bouquetChangeCB = None, serviceChangeCB = None, isEPGBar = None, switchBouquet = None, EPGNumberZap = None, togglePiP = None):
    orig_EPGSel__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, isEPGBar, switchBouquet, EPGNumberZap, togglePiP)

def My_EPGSelATV__init__(self, session, service = None, zapFunc = None, eventid = None, bouquetChangeCB = None, serviceChangeCB = None, EPGtype = None, StartBouquet = None, StartRef = None, bouquets = None):
    orig_EPGSel__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, EPGtype, StartBouquet, StartRef, bouquets)

def My_EPGSelPLI__init__(self, session, service = None, zapFunc = None, eventid = None, bouquetChangeCB = None, serviceChangeCB = None, parent = None):
    orig_EPGSel__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, parent)

def main(session, **kwargs):
    session.open(translatorMain, None)
    return

def Plugins(**kwargs):
    return [
     PluginDescriptor(name='EPG Translator', description='Translate your EPG', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main),
     PluginDescriptor(name='EPG Translator', description='Translate your EPG', where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main),
     PluginDescriptor(name='EPG Translator', description='Translate your EPG', where=[PluginDescriptor.WHERE_EVENTINFO], fnc=main),
     PluginDescriptor(name='EPG Translator', description='Translate your EPG', where=[PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)
    ]
