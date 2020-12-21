# Skin data for screenwidth <= 1280
# Only contains "class" data.  No instance data
#

class MySkinData:

# class translatorConfig bits
#
    translatorConfig_skin = """
        <screen position="center,center" size="545,525" backgroundColor="#20000000" title="EPG Translator Setup">
            <ePixmap position="0,0" size="545,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/translatorConfig.png" alphatest="blend" zPosition="1" />
            <ePixmap position="10,59" size="525,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/separator.png" alphatest="off" zPosition="1" />
            <widget name="config" position="10,60" size="525,125" itemHeight="25" scrollbarMode="showOnDemand" font="Regular;18" secondfont="Regular;18" zPosition="1" />
            <ePixmap position="10,186" size="525,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/separator.png" alphatest="off" zPosition="1" />
            <ePixmap position="125,196" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/buttons/green.png" alphatest="blend" zPosition="1" />
            <ePixmap position="350,196" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/buttons/red.png" alphatest="blend" zPosition="1" />
            <eLabel position="150,195" size="180,20" font="Regular;18" halign="left" text="Save" transparent="1" zPosition="1" />
            <eLabel position="375,195" size="180,20" font="Regular;18" halign="left" text="Cancel" transparent="1" zPosition="1" />
            <widget name="flag" position="128,225" size="288,288" alphatest="blend" zPosition="1" />
        </screen>
        """

# class translatorMain bits
#
#   "text" y-size is dynamic {size}
#
    translatorMain_skin = """
        <screen position="center,80" size="1000,610" title="EPG Translator">
            <ePixmap position="0,0" size="1000,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/translator.png" alphatest="blend" zPosition="1" />
            <ePixmap position="10,6" size="36,36" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EPGTranslator/pic/buttons/blue.png" alphatest="blend" zPosition="2" />
            <widget name="label" position="34,6" size="200,40" font="Regular;24" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2" />
            <widget render="Label" source="global.CurrentTime" position="740,0" size="240,50" font="Regular;24" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
            <convert type="ClockToText">Format:%H:%M:%S</convert>
            </widget>
            <widget name="flag" position="10,40" size="288,288" alphatest="blend" zPosition="1" />
            <widget name="flag2" position="10,325" size="288,288" alphatest="blend" zPosition="1" />
            <widget name="text" position="308,60" size="750,{size}" font="Regular;24" halign="left" zPosition="2" />
            <widget name="text2" position="308,345" size="750,270" font="Regular;24" halign="left" zPosition="1" />
        </screen>
        """
    tMyes = "270"
    tMno  = "555"


MySD = MySkinData()
