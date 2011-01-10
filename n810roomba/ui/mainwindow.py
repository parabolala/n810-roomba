from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from n810roomba.ui.mainwindow_ui import Ui_MainWindow

KEYS_COMMANDS = {
        Qt.Key_Up: '<Up>',
        Qt.Key_Down: '<Down>',
        Qt.Key_Left: '<Left>',
        Qt.Key_Right: '<Right>',
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
    def __init__(self, bot, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setupUi(self)
        self.text_cli.keyPressEvent = key_processor(self)

        self.bot = bot


    @property
    def speed(self):
        return self.slider_speed.value()

    def sendCommand(self, command):
        if not command:
            return
        print 'Command: ', command
        self.text_cli.clear()

        c = command

        if c == ' ':
            self.bot.Stop()
        elif c == '<Up>':
            self.bot.DriveStraight(self.speed)
        elif c == '<Down>':
            self.bot.DriveStraight(-self.speed)
        elif c == '<Left>':
            self.bot.TurnInPlace(self.speed, 'ccw')
        elif c == '<Right>':
            self.bot.TurnInPlace(self.speed, 'cw')




