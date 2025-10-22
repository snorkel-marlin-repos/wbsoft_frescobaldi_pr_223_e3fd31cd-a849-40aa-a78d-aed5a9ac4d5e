# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The help browser window.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import helpers
import icons

from . import __path__
from . import helpimpl


class Window(QMainWindow):
    """The help browser window."""
    def __init__(self):
        super(Window, self).__init__()
        self.setAttribute(Qt.WA_QuitOnClose, False)
        
        self.browser = Browser(self)
        self.setCentralWidget(self.browser)
        
        self._toolbar = tb = self.addToolBar('')
        self._back = tb.addAction(icons.get('go-previous'), '')
        self._forw = tb.addAction(icons.get('go-next'), '')
        self._home = tb.addAction(icons.get('go-home'), '')
        self._toc = tb.addAction(icons.get('help-contents'), '')
        self._print = tb.addAction(icons.get('document-print'), '')
        self._back.triggered.connect(self.browser.backward)
        self._forw.triggered.connect(self.browser.forward)
        self._home.triggered.connect(self.home)
        self._toc.triggered.connect(self.toc)
        self._print.triggered.connect(self.print_)
        
        self.browser.sourceChanged.connect(self.slotSourceChanged)
        self.browser.historyChanged.connect(self.slotHistoryChanged)
        app.translateUI(self)
        self.loadSettings()
    
    def closeEvent(self, ev):
        self.saveSettings()
        super(Window, self).closeEvent(ev)
        
    def loadSettings(self):
        self.resize(QSettings().value("helpbrowser/size", QSize(400, 300)))
    
    def saveSettings(self):
        QSettings().setValue("helpbrowser/size", self.size())
    
    def translateUI(self):
        self.setCaption()
        self._toolbar.setWindowTitle(_("Toolbar"))
        self._back.setText(_("Back"))
        self._forw.setText(_("Forward"))
        self._home.setText(_("Start"))
        self._toc.setText(_("Contents"))
        self._print.setText(_("Print"))
        
    def slotSourceChanged(self):
        self.setCaption()
    
    def setCaption(self):
        title = self.browser.documentTitle() or _("Help")
        self.setWindowTitle(app.caption(title) + " " + _("Help"))

    def slotHistoryChanged(self):
        self._back.setEnabled(self.browser.isBackwardAvailable())
        self._forw.setEnabled(self.browser.isForwardAvailable())
    
    def home(self):
        self.displayHelp('contents')
        
    def toc(self):
        self.displayHelp('toc')
    
    def displayHelp(self, page):
        """Opens the help browser showing the specified help page (by name or class)."""
        if isinstance(page, type) and issubclass(page, helpimpl.page):
            page = page.name
        self.browser.setSource(QUrl("help:{0}".format(page)))
        self.show()
        self.activateWindow()
        self.raise_()
    
    def print_(self):
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle(app.caption(_("Print")))
        options = (QAbstractPrintDialog.PrintToFile
                   | QAbstractPrintDialog.PrintShowPageSize
                   | QAbstractPrintDialog.PrintPageRange)
        if self.browser.textCursor().hasSelection():
            options |= QAbstractPrintDialog.PrintSelection
        dlg.setOptions(options)
        if dlg.exec_():
            self.browser.print_(printer)


class Browser(QTextBrowser):
    def __init__(self, parent):
        super(Browser, self).__init__(parent)
        app.settingsChanged.connect(self.reload, 1)
        self.anchorClicked.connect(self.slotAnchorClicked)
        self.setOpenLinks(False)
        
    def slotAnchorClicked(self, url):
        if url.scheme() == "help":
            self.setSource(url)
        else:
            helpers.openUrl(url)
        
    def loadResource(self, type, url):
        if type == QTextDocument.HtmlResource:
            return helpimpl.html(url.path())
        elif type == QTextDocument.ImageResource:
            url = QUrl.fromLocalFile(os.path.join(__path__[0], url.path()))
        return super(Browser, self).loadResource(type, url)
    
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and int(ev.modifiers()) == 0:
            self.window().close()
        super(Browser, self).keyPressEvent(ev)


