# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

import sys


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pbAlert = QtWidgets.QPushButton(Dialog)
        self.pbAlert.setObjectName("pbAlert")
        self.verticalLayout.addWidget(self.pbAlert)
        self.pbGetWebWidth = QtWidgets.QPushButton(Dialog)
        self.pbGetWebWidth.setObjectName("pbGetWebWidth")
        self.verticalLayout.addWidget(self.pbGetWebWidth)
        self.viewLayout = QtWidgets.QHBoxLayout()
        self.viewLayout.setSpacing(6)
        self.viewLayout.setObjectName("viewLayout")
        self.verticalLayout.addLayout(self.viewLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.pbAlert.setText(_translate("Dialog", "javascript function execute"))
        self.pbGetWebWidth.setText(_translate("Dialog", "emit signals"))

class bridge(QObject):
    sendText = QtCore.pyqtSignal()
    signal_1 = QtCore.pyqtSignal()

    def __init__(self, dialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
        dialog.ui.pbGetWebWidth.clicked.connect(self.signal_1)
        # dialog.ui.pbGetWebWidth.clicked.connect(self.sendText)

    def instance(self):
        return bridge()

    @QtCore.pyqtSlot(str)
    def showMsgBox(self, s):
        print(s)

    @QtCore.pyqtSlot(str)
    def test(self, s):
        print('bridge.test():', s)

class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.m_view = QWebEngineView(self)
        self.channel = QWebChannel(self)
        self.b = bridge(self)

        self.channel.registerObject('b', self.b)
        self.m_view.page().setWebChannel(self.channel)
        self.m_view.page().load(QUrl("file:///index.html"))

        self.ui.viewLayout.addWidget(self.m_view)
        # js_str = '''window.bridge.showMsgBox()'''
        js_str = '''alert('from runJavaScript')'''
        self.ui.pbAlert.clicked.connect(lambda: self.m_view.page().runJavaScript(js_str, self.callback))
        # self.ui.pbAlert.clicked.connect(lambda: self.b.sendText.emit())

        # self.ui.pbGetWebWidth.clicked.connect(lambda: self.b.sendText.emit())

        # self.b.sendText.connect(lambda: print('b.sendText.emit():'))
        # self.b.signal_1.connect(lambda: print('b.signal_1.emit():'))

    def __del__(self):
        del self.ui

    def callback(self, v):
        print('callback:', v)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Dialog()
    w.show()
    app.exec_()


