import time
import Queue
import re
import logging
import threading
from urlparse import urlparse

from PyQt4 import QtNetwork
from PyQt4 import QtGui, QtCore, Qt as Qt_mod
from PyQt4.QtCore import Qt

from n810roomba.ui.mainwindow_ui import Ui_MainWindow

log = logging.getLogger(__name__)

KEYS_COMMANDS = {
        Qt.Key_Up: '<Up>',
        Qt.Key_Down: '<Down>',
        Qt.Key_Left: '<Left>',
        Qt.Key_Right: '<Right>',
        }

CONTROLLER_FPS = 10.
CONTROLLER_PERIOD = 1 / CONTROLLER_FPS

class DriverInput(object):
    __slots__ = ['speed',  # 0 ..
                 'is_accelerating',  # -1, 0, 1
                 'is_steering',  # -1, 0, 1
                 ]

    def __init__(self):
        self.speed = 0
        self.is_accelerating = 0
        self.is_steering = 0

class Driver(threading.Thread):

    def __init__(self, bot):
        self.bot = bot
        self.finish = False
        self.input = DriverInput()
        self.wakeup = threading.Event()
        self.lock = threading.RLock()

        super(Driver, self).__init__()

    def step(self):
        speed = self.input.is_accelerating * 200

        steering = self.input.is_steering
        r = None
        if steering == 0:
            if speed:
                r = 32768
            else:
                r = 0
        else:
            r = steering / abs(steering)
            if speed != 0:
                r *= 500
            else:
                speed = 500

        return (speed, r)

    def end(self):
        self.finish = True
        self.wakeup.set()

    def sensors(self):
        return self.bot.sensors.GetAll()

    def run(self):
        while True:
            self.wakeup.wait(CONTROLLER_PERIOD)
            self.wakeup.clear()
            if self.finish:
                break
            with self.lock:
                velocity, radius = self.step()

                #if velocity != 0 or radius != 0:
                self.bot.Drive(velocity, radius)

content_type_pattern = re.compile(r'([^;]+);boundary=(\S*)')

class KeyProcessor(object):
    def __init__(self, window, released=False):
        self.window = window
        self.released = released

    def __call__(self, event):
        key = event.key()
        if key in KEYS_COMMANDS:
            self.window.sendCommand(KEYS_COMMANDS[key], released=self.released)
        else:
            txt = self.window.text_cli
            QtGui.QLineEdit.keyPressEvent(txt, event)

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, bot, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setupUi(self)
        self.text_cli.keyPressEvent = KeyProcessor(self)
        self.text_cli.keyReleaseEvent = KeyProcessor(self, released=True)

        self.bot = bot
        self.driver = Driver(self.bot)
        self.driver.start()

        self.image = QtGui.QImage()
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(self.image))

        self.text_cli.setFocus()

        self.bytes = ''
        url = 'http://192.168.1.14:8080/videofeed'
        self.url = urlparse(url)
        self.qnam = QtNetwork.QNetworkAccessManager()
        path = self.url.path
        if self.url.query:
            path += '?' + self.url.query
        log.info('getting %s', path)
        self.boundary = None
        self.reply = self.qnam.get(QtNetwork.QNetworkRequest(QtCore.QUrl(url)))
        self.connect(self.reply, QtCore.SIGNAL('readyRead()'), self.update_image)

        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.update_sensors)
        self.timer.start(500)

    def parse_header(self):
        content_type = self.reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader).toString()
        matches = content_type_pattern.findall(content_type)
        if not matches or matches[0][0] != 'multipart/x-mixed-replace':
            logging.error('Invalid header: %s', content_type)

        self.boundary = matches[0][1]

    def strip_frame_headers(self, frame_data):
        return '\r\n'.join(frame_data.split('\r\n')[3:])

    def update_image(self):
        first_frame = False
        data = self.reply.readAll().data()
        self.bytes += data
        if self.boundary is None:
            first_frame = True
            self.parse_header()
        try:
            pos = self.bytes.index(self.boundary)
            image = self.strip_frame_headers(self.bytes[:pos])
            self.bytes = self.bytes[pos + len(self.boundary):]
            self.image.loadFromData(image)
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(self.image))
            if first_frame:
                self.image_label.adjustSize()
        except ValueError:
            return
        #self.sensors_text.setText("asd")

    def finish(self):
        self.driver.end()
        #self.timer.stop()

    @property
    def speed(self):
        return self.slider_speed.value()

    def update_sensors(self):
        values = self.driver.sensors()
        res = []

        for k, v in values.items():
            res.append('%s: %s' % (k, v))
        s = '\n'.join(res)

        self.sensors_text.setText(s)

    def sendCommand(self, command, released=False):
        if not command:
            return
        print 'Command:', 'released' if released else '', command
        self.text_cli.clear()

        c = command

        is_accelerating = self.driver.input.is_accelerating
        is_steering = self.driver.input.is_steering
        speed = self.speed

        if c == ' ':
            pass
        elif c == '<Up>':
            is_accelerating = 0 if released else 1
        elif c == '<Down>':
            is_accelerating = 0 if released else -1
        elif c == '<Left>':
            is_steering = 0 if released else 1
        elif c == '<Right>':
            is_steering = 0 if released else -1

        self.driver.input.speed = speed
        self.driver.input.is_steering = is_steering
        self.driver.input.is_accelerating = is_accelerating


