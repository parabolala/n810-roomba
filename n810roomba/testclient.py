import time
import logging

from n810roomba import common, errors


log = logging.getLogger('client')


def main():
    client = common.RoombaClient()

    try:
        client.connect()
    except errors.PortNameRequired, e:
        ports = client.facade.get_ports()
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

        client.connect(tty=tty)

    bot = client.bot

    bot.Control()
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
