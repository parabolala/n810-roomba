import traceback
import time
import logging

from n810roomba import common, errors
from n810roomba.client import RemoteClient, LocalBot


log = logging.getLogger(__name__)


def main():
    try:
        client = RemoteClient()

        try:
            client.connect()
        except errors.PortNameRequired, e:
            ports = client.facade.get_ports()
            if not ports:
                logging.critical('No tty to connect to')
            tty = common.pick_one(ports, "Select a port to connect:")

            logging.info('Using serial port %s' % tty)

            client.connect(tty=tty)

        bot = client.bot
    except Exception:
        #traceback.print_exc()
        #bot = LocalBot()
        raise


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
