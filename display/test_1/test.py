#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import PyQt5
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView

class CallHandler(QObject):

    _signal1 = PyQt5.QtCore.pyqtSignal(str)
    _signal2 = PyQt5.QtCore.pyqtSignal(str)
    
    @pyqtSlot(result=str)
    def _slot1(self):
        print('_slot1')
        return 'hello, Python'

    @pyqtSlot(result=str)
    def _slot2(self):
        print('_slot2')
        return 'hello, Python'


class SC(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.view = QWebEngineView(self)

        self.channel = QWebChannel()
        self.handler = CallHandler()
        self.channel.registerObject('pyjs', self.handler)
        self.view.page().setWebChannel(self.channel)

        self.handler._signal1.connect(self.handler._slot1)
        #self.handler._signal2.connect(self.handler._slot2)

        b1 = QPushButton("b1", self)
        b1.clicked.connect(self.s1s)

        #b2 = QPushButton("b2", self)
        #b2.clicked.connect(self.s2s)

        url_string = "file:///test.html"
        self.view.load(QUrl(url_string))
        self.setGeometry(300, 300, 300, 220)
        self.show()

    def s1s(self):
        self.handler._signal1.emit("b1")

    def s2s(self):
        self.handler._signal2.emit("b2")




    


if __name__ == '__main__':
    app = QApplication(sys.argv)

    s = QWidget()
    view = QWebEngineView(s)
    channel = QWebChannel(view)
    handler = CallHandler()
    channel.registerObject('pyjs', handler)
    handler._signal1.connect(handler._slot1)

    view.page().setWebChannel(channel)

    b1 = QPushButton("b1", s)
    #b1.clicked.connect()

    url_string = "file:///test.html"
    view.load(QUrl(url_string))
    s.setGeometry(300, 300, 300, 220)

    s.show()
    sys.exit(app.exec_())