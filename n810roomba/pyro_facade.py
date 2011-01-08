import Pyro.core
import pyrobot


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
        sci = RoombaSCI(tty, baud)
        self.daemon.connect(sci, pyro_name)
