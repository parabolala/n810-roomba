from glob import glob
import sys
import logging

from Pyro.errors import NamingError
import Pyro.core

import pyrobot


log = logging.getLogger('facade')

class RoombaSCI(Pyro.core.ObjBase, pyrobot.SerialCommandInterface):
    def __init__(self, tty='/dev/ttyUSB0', baud=115200):
        pyrobot.SerialCommandInterface.__init__(self, tty=tty, baudrate=baud)
        Pyro.core.ObjBase.__init__(self)


class RoombaFacade(Pyro.core.ObjBase):
    def __init__(self, daemon):
        self.daemon = daemon
        super(RoombaFacade, self).__init__()

    def __getstate__(self):
        d = self.__dict__.copy()
        d.pop('daemon')
        return d

    def make_sci(self, pyro_name, tty, baud):
        log.info('Creating SCI: %s %s %s' % (pyro_name, tty, baud))
        sci = RoombaSCI(tty, baud)
        try:
            self.daemon.getNameServer().unregister(pyro_name)
        except NamingError:
            pass
        self.daemon.connect(sci, pyro_name)

    def get_ports_posix(self):
        return glob('/dev/ttyUSB*')

    def get_ports_darwin(self):
        return glob('/dev/cu.usbserial*')

    def get_ports(self):
        func = {
                'linux2': self.get_ports_posix,
                'darwin': self.get_ports_darwin,
                }.get(sys.platform)
        if not func:
            return None
        else:
            return func()

