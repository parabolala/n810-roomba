import time
import logging
from pprint import pprint

import pyrobot
from n810roomba.pyro_facade import RoombaFacade

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def get_local():
    facade = RoombaFacade(None)
    ports = facade.get_ports()

    log.debug('Found serial ports: %s' % unicode(ports))
    #client = common.RoombaClient()


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
    elif len(ports) == 1:
        tty = ports[0]
    else:
        raise AssertionError("No serial port found")

    logging.info('Using serial port %s' % tty)

    bot = pyrobot.Roomba(tty=tty, baud=115200)

    bot.Control()

    return bot


def main():
    bot = get_local()
    pprint(bot.sensors.GetAll())
    bot.Drive(40, 200)
    time.sleep(0.7)
    bot.Drive(-40, -200)
    time.sleep(0.7)
    bot.Drive(40, 200)
    time.sleep(0.7)
    bot.Drive(-40, -200)
    time.sleep(0.7)
    bot.Drive(0, 0)

if __name__ == '__main__':
    main()

