from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from n810roomba.ui.mainwindow_ui import Ui_MainWindow

KEYS_COMMANDS = {
        Qt.Key_Up: '<Up>',
        Qt.Key_Down: '<Down>',
        Qt.Key_Left: '<Left>',
        Qt.Key_Right: '<Right>',
        Qt.Key_Space: '<Space>',
        }

def key_processor(window):
    def process_arrows(event):
        key = event.key()
        if key in KEYS_COMMANDS:
            window.sendCommand(KEYS_COMMANDS[key])
        else:
            txt = window.text_cli
            QtGui.QLineEdit.keyPressEvent(txt, event)
    return process_arrows

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setupUi(self)
        self.text_cli.keyPressEvent = key_processor(self)

    def sendCommand(self, command):
        if not command:
            return
        print 'Command: ', command
        self.text_cli.clear()

