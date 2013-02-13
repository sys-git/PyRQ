'''
Created on 11 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, QtCore
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers

class FilterConfig(object):
    def __init__(self, ref, key, settings, font=None, palette=None):
        self.ref = ref
        self.key = key
        self.settings = settings
        self.defaults(font=font, palette=palette)
    def defaults(self, font=None, palette=None):
        self.setBackgroundColour(QtGui.QColor(255, 255, 255))
        self.setTextColour(QtGui.QColor(0, 0, 0))
        self.setFont(font)
    def backgroundColour(self):
        return self._backgroundColour
    def font(self):
        return self._font
    def textColour(self):
        return self._textColour
    def setBackgroundColour(self, backgroundColour):
        self._backgroundColour = backgroundColour
    def setFont(self, font):
        self._font = font
    def setTextColour(self, textColour):
        self._textColour = textColour
    def __neq__(self, other):
        return not self.__eq__(other)
    def __eq__(self, other):
        if not isinstance(other, FilterConfig):
            return False
        if other.backgroundColour()!=self._backgroundColour:
            return False
        if other.font()!=self._font:
            return False
        if other.textColour()!=self._textColour:
            return False
        if other.ref!=self.ref:
            return False
        if other.key!=self.key:
            return False
        return True
    def dump(self):
        self.settings.beginGroup("filters")
        try:
            self.settings.beginGroup(self.ref)
            try:
                self.export_(self.settings)
            finally:
                self.settings.endGroup()
        finally:
            self.settings.endGroup()
    def export_(self, settings):
        settings.beginGroup(self.key)
        try:
            #    Background colour:
            backgroundColour = self.backgroundColour()
            if backgroundColour!=None:
                settings.setValue("backgroundColour", backgroundColour.rgba())
            #    Text colour:
            textColour = self.textColour()
            if textColour!=None:
                settings.setValue("textColour", textColour.rgba())
            #    Font:
            font = self.font()
            if font!=None:
                settings.setValue("font", font.toString())
        finally:
            settings.endGroup()
    def load(self):
        self.settings.beginGroup("filters")
        try:
            self.settings.beginGroup(self.ref)
            try:
                self.import_(self.settings)
            finally:
                self.settings.endGroup()
        finally:
            self.settings.endGroup()
    def import_(self, settings):
        settings.beginGroup(self.key)
        try:
            #    Background colour:
            (value, isValid) = settings.value("backgroundColour").toUInt()
            if isValid==True:
                self.setBackgroundColour(QtGui.QColor())
                self.backgroundColour().setRgba(value)
            #    Text colour:
            (value, isValid) = settings.value("textColour").toUInt()
            if isValid==True:
                self.setTextColour(QtGui.QColor())
                self.textColour().setRgba(value)
            #    Font:
            value = settings.value("font")
            if value.isValid()==True:
                value = value.toString()
                self.setFont(QtGui.QFont())
                self.font().fromString(value)
        finally:
            settings.endGroup()
    def exportAs(self, settings, name):
        settings.beginGroup(name)
        try:
            self.export_(settings)
        finally:
            settings.endGroup()
    def importFrom(self, settings, name):
        settings.beginGroup(name)
        try:
            self.import_(settings)
        finally:
            settings.endGroup()
    def getConfig(self):
        s = ["%(R)s.%(K)s/START"%{"R":self.ref, "K":self.key}]
        if self._backgroundColour!=None:
            s.append("backgroundColour.red: %(R)s"%{"R":self._backgroundColour.red()})
            s.append("backgroundColour.green: %(R)s"%{"R":self._backgroundColour.green()})
            s.append("backgroundColour.blue: %(R)s"%{"R":self._backgroundColour.blue()})
        else:
            s.append("backgroundColour: None")
        if self._textColour!=None:
            s.append("textColour.red: %(R)s"%{"R":self._textColour.red()})
            s.append("textColour.green: %(R)s"%{"R":self._textColour.green()})
            s.append("textColour.blue: %(R)s"%{"R":self._textColour.blue()})
        else:
            s.append("textColour: None")
        if self._font!=None:
            s.append("font.toString: %(R)s"%{"R":self._font.toString()})
        else:
            s.append("font: None")
        s.append("%(R)s.%(K)s/END"%{"R":self.ref, "K":self.key})
        ss = "\r".join(s)
        return ss
    def getExistingUserActionFilterNames(self, settings=None):
        if settings==None:
            settings = self.settings
        return settings.childGroups()

class FiltersConfig(object):
    def __init__(self, settings, ref, font=None, palette=None):
        self.settings = settings
        self.ref = ref
        self._font = font
        self.palette = palette
        self._configs = {
                         Enablers.PUT_START:FilterConfig(ref, Enablers.PUT_START, settings, font=font, palette=palette),
                         Enablers.PUT_END:FilterConfig(ref, Enablers.PUT_END, settings, font=font, palette=palette),
                         Enablers.GET_START:FilterConfig(ref, Enablers.GET_START, settings, font=font, palette=palette),
                         Enablers.GET_END:FilterConfig(ref, Enablers.GET_END, settings, font=font, palette=palette),
                         Enablers.CREATE_START:FilterConfig(ref, Enablers.CREATE_START, settings, font=font, palette=palette),
                         Enablers.CREATE_END:FilterConfig(ref, Enablers.CREATE_END, settings, font=font, palette=palette),
                         Enablers.CLOSE_START:FilterConfig(ref, Enablers.CLOSE_START, settings, font=font, palette=palette),
                         Enablers.CLOSE_END:FilterConfig(ref, Enablers.CLOSE_END, settings, font=font, palette=palette),
                         Enablers.QSIZE_START:FilterConfig(ref, Enablers.QSIZE_START, settings, font=font, palette=palette),
                         Enablers.QSIZE_END:FilterConfig(ref, Enablers.QSIZE_END, settings, font=font, palette=palette),
                         Enablers.MAXQSIZE_START:FilterConfig(ref, Enablers.MAXQSIZE_START, settings, font=font, palette=palette),
                         Enablers.MAXQSIZE_END:FilterConfig(ref, Enablers.MAXQSIZE_END, settings, font=font, palette=palette),
                         }
    def backgroundColour(self, action):
        return self._configs[action].backgroundColour()
    def font(self, action):
        what = self._configs[action]
        font = what.font()
        if font==None:
            font = self._font
        return font
    def textColour(self, action):
        return self._configs[action].textColour()
    def clone(self):
        fc = FiltersConfig(self.settings, self.ref, font=self._font, palette=self.palette)
        for i, k in self._configs.items():
            fc._configs[i] = k
        return fc
    def dump(self):
        for value in self._configs.values():
            value.dump()
    def export_(self, filename):
        #    Dump every settings to the given ini filename:
        settings = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
        for value in self._configs.values():
            value.export_(settings)
    def import_(self, filename):
        #    Dump every settings to the given ini filename:
        settings = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
        for value in self._configs.values():
            value.import_(settings)
        return self
    def load(self):
        for value in self._configs.values():
            value.load()
    def getConfig(self):
        s = []
        for key, value in self._configs.items():
            s.append("ACTION: %(A)s"%{"A":key})
            s.append(value.getConfig())
        ss = "\n".join(s)
        return ss
    def create(self, font, palette):
        return FiltersConfig(self.settings, self.ref, font=font, palette=palette)
    def setFont(self, font):
        self._font = font
    def update(self, action, newConfig):
        self._configs[action].setFont(newConfig.font(action))
        self._configs[action].setBackgroundColour(newConfig.backgroundColour(action))
        self._configs[action].setTextColour(newConfig.textColour(action))
    def exportAs(self, action, name, settings=None):
        if settings==None:
            settings = self.settings
        settings.beginGroup("user")
        try:
            settings.beginGroup("actionFilters")
            try:
                self._configs[action].exportAs(settings, name)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
    def importFrom(self, action, name, settings=None):
        if settings==None:
            settings = self.settings
        settings.beginGroup("user")
        try:
            settings.beginGroup("actionFilters")
            try:
                self._configs[action].importFrom(settings, name)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
    def getExistingUserActionFilterNames(self, action, settings=None):
        if settings==None:
            settings = self.settings
        settings.beginGroup("user")
        try:
            settings.beginGroup("actionFilters")
            try:
                return self._configs[action].getExistingUserActionFilterNames(settings=settings)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()



