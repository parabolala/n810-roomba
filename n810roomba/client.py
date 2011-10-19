import logging

import threading
import pyrobot

import Pyro.naming

from Pyro.errors import NamingError

from n810roomba import settings, errors
from n810roomba.common import pick_one
from n810roomba.pyro_facade import RoombaFacade


log = logging.getLogger(__name__)


def LocalBot():
    facade = RoombaFacade(None)
    ports = facade.get_ports()

    log.debug('Found serial ports: %s' % unicode(ports))
    #client = common.RoombaClient()

    if not ports:
        raise AssertionError("No serial port found")
    tty = pick_one(ports, "Select a port to connect:")

    logging.info('Using serial port %s' % tty)

    bot = pyrobot.Roomba(tty=tty, baud=115200)

    bot.Control()

    return bot


class RemoteClient(object):
    """Connects to remote pyro facade object"""
    facade = None
    ns = None

    def __init__(self, facade_name=None, sci_name=None):
        self.facade_name = facade_name or settings.PYRO_FACADE_NAME
        self.sci_name = sci_name or settings.PYRO_SCI_NAME
        self.bot = None

    def connect(self, tty=None, baud=None):
        self.facade = self.get_facade()

        ports = self.facade.get_ports()

        if not tty and len(ports) == 1:
            tty = ports[0]
        elif tty and tty in ports:
            pass
        else:
            raise errors.PortNameRequired()

        log.debug('Requesting sci at %s' % self.sci_name)
        self.facade.make_sci(self.sci_name, tty=tty,
                      baud=baud or 115200)

        log.debug('Retrieving sci from %s' % self.sci_name)
        sci = self.get_from_pyro(self.sci_name)
        # TODO: solve this adequately.
        sci.lock = threading.RLock()

        self.bot = pyrobot.Roomba(notty=True)
        self.bot._set_sci(sci)

    def get_facade(self, facade_name=None):
        if facade_name is None:
            facade_name = self.facade_name

        facade = self.get_from_pyro(facade_name)

        return facade

    def get_from_pyro(self, name):
        if self.ns is None:
            locator = Pyro.naming.NameServerLocator()
            self.ns = locator.getNS()
        ns = self.ns

        try:
            log.debug('Looking for object %s' % name)
            uri = ns.resolve(name)
            log.debug('Found object at %s' % uri)
        except NamingError, x:
            log.critical('Couldn\'t find object, nameserver says:' % x)
            raise

        obj = Pyro.core.getProxyForURI(uri)

        return obj
