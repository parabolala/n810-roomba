import time
import logging

import pyrobot

import Pyro.naming
from Pyro.errors import NamingError

import settings


log = logging.getLogger('client')


def main():
    locator = Pyro.naming.NameServerLocator()
    ns = locator.getNS()
    try:
        log.info('Looking for facade')
        URI = ns.resolve(settings.PYRO_FACADE_NAME)
        log.info('Found facade at %s' % URI)
    except NamingError,x:
        log.critical('Couldn\'t find object, nameserver says:' % x)
        raise SystemExit()

    facade = Pyro.core.getProxyForURI(URI)

    log.debug('Requesting sci at %s' % settings.PYRO_FACADE_NAME)

    ports = facade.get_ports()
    if len(ports) > 1:
        print "Select a port to connect:"
        for i, port in enumerate(ports):
            print i, port
        port_num = raw_input('[0]> ')
        try:
            port_num = int(port_num)
            if not 0 <= port_num < len(ports):
                raise ValueError
        except ValueError:
            port_num = 0
            print 'Using 0: %s' % ports[port_num]
        tty = ports[port_num]
    elif not ports:
        logging.critical('No tty to connect to')
        raise SystemExit()
    else:
        tty = ports[0]

    logging.info('Using serial port %s' % tty)

    facade.make_sci(settings.PYRO_SCI_NAME, tty=tty,
                  baud=115200)

    sci = Pyro.core.getProxyForURI(ns.resolve(settings.PYRO_SCI_NAME))

    bot = pyrobot.Roomba(notty=True)
    bot._set_sci(sci)


    bot.Control()
    bot.Drive(40, 1)
    time.sleep(0.5)
    bot.Drive(-40, 1)
    time.sleep(0.5)
    bot.Drive(0, 0)

if __name__ == '__main__':
    main()
