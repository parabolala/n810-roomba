import logging

import pyrobot

import Pyro.naming
from Pyro.errors import NamingError

from n810roomba import settings, errors


log = logging.getLogger('common')

class RoombaClient(object):
    facade = None
    ns = None

    def __init__(self, facade_name=None, sci_name=None):
        self.facade_name = facade_name or settings.PYRO_FACADE_NAME
        self.sci_name = sci_name or settings.PYRO_SCI_NAME

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

