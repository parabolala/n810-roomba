import functools
import datetime
import time
import logging
import threading
import traceback
import urlparse

from tornado import ioloop, web
from tornado.websocket import WebSocketHandler

from n810roomba import common, errors
from n810roomba.web.conf import settings
from n810roomba.web.image import ImageHandler
from n810roomba.web.dispatcher import Dispatcher

from n810roomba.client import LocalBot, RemoteClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_class_logger(class_or_inst):
    if isinstance(class_or_inst, type):
        klass = class_or_inst
    else:
        klass = class_or_inst.__class__
    return logging.getLogger('%s.%s' % (__name__, klass.__name__))


def make_bot():
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
        traceback.print_exc()
        bot = LocalBot()
    return bot


class BotHolder_(object):
    _lock = threading.RLock()
    _sensors_probe_interval = datetime.timedelta(seconds=1)
    _bot = None
    interesting_sensors = ['charge', 'capacity', 'bump-right', 'bump-left']

    def __init__(self):
        self.log = get_class_logger(self)
        self._ioloop = ioloop.IOLoop.instance()
        self._publication = None
        self._last_sensors_state = []

    def _start_publishing_sensors(self):
        sensors = self._bot.sensors.GetAll()
        self._maybe_notify_sensors(sensors)

        self._publication = self._ioloop.add_timeout(
            self._sensors_probe_interval, self._start_publishing_sensors)

    def _maybe_notify_sensors(self, sensors):
        last = self._last_sensors_state
        if not last:
            last = dict((k, None) for k in self.interesting_sensors)

        values = dict((k, sensors.get(k)) for k in self.interesting_sensors)

        changed_values = dict((name, value) for name, value in values.items()
                                    if last[name] != value)
        self._last_sensors_state = values

        if changed_values:
            Dispatcher.notify('sensors-data', changed_values)

    def _stop_publishing_sensors(self):
        if self._publication is None:
            return
        else:
            self._ioloop.remove_timeout(self._publication)

    @property
    def bot(self):
        with self._lock:
            if self._bot:
                if self._is_alive():
                    bot = self._bot
                else:
                    self.log.info('bot died')
                    self._stop_publishing_sensors()
                    self._bot = None
                    bot = None
            else:
                try:
                    bot = make_bot()
                    self._bot = bot
                    self.log.info('bot was born')
                    self._start_publishing_sensors()
                except AssertionError:
                    bot = None
                self._bot = bot
            return self._bot

    def _is_alive(self):
        if not self._bot:
            return False

        try:
            sensors = self._bot.sensors.GetAll()
        except Exception:
            return False
        if sensors:
            return True
        else:
            return False

BotHolder = BotHolder_()
def control(value):
    directions = {'left': value & 8,
                  'up': value & 4,
                  'right': value & 2,
                  'down': value & 1,}
    down = 1
    right = 2
    up = 4
    left = 8

    radius = 32768
    if value & up:
        speed = 200
    elif value & down:
        speed = -200
    else:
        if value & (left | right):
            speed = 200
        else:
            speed = 0
            radius = 0

    if value & right:
        if value & (up | down):
            radius = -200
        else:
            radius = -1
    elif value & left:
        if value & (up | down):
            radius = 200
        else:
            radius = 1
    log.debug('driving %d, %d' % (speed, radius))
    bot = BotHolder.bot

    if bot:
        try:
            bot.Drive(speed, radius)
        except Exception:
            pass



class UsersContainer_(object):
    _users = []

    def __init__(self):
        self.log = get_class_logger(UsersContainer_)
        self._dispatcher = Dispatcher
        self._dispatcher.subscribe('user added_meta', self._new_subscriber)

    def _new_subscriber(self, event):
        action, callback = event
        if action == 'add':
            for user in self._users:
                callback(user.as_dict())

    def add_user(self, user):
        self.log.info('user added: %s', user)
        self._users.append(user)
        self._dispatcher.notify('user added', user.as_dict())

    def remove_user(self, user):
        self.log.info('user removed: %s', user)
        self._dispatcher.notify('user removed', user.as_dict())

        # TODO: somehow i get here twice for some users
        if user in self._users:
            self._users.remove(user)

    def change_name(self, user, from_name, to_name):
        self.log.info('renaming: %s -> %s', from_name, to_name)
        self._dispatcher.notify('user renamed', (user.as_dict(), to_name))

    def subscribe_all(self, callback):
        for ev in ['added', 'removed', 'renamed']:
            ev_name = 'user ' + ev
            @functools.wraps(callback)
            def cb(arg, ev_name=ev_name):
                callback((ev_name, arg))
            self._dispatcher.subscribe(ev_name, cb)
    def unsubscribe_all(self, callback):
        self._dispatcher.unsubscribe_all(callback)

    def get_users(self):
        return self._users
UsersContainer = UsersContainer_()


class CircularDoubleLinkedList(object):
    class Node(object):
        counter = 0
        def __init__(self, val):
            self.val = val
            self.id = CircularDoubleLinkedList.Node.counter
            CircularDoubleLinkedList.Node.counter += 1

        def __repr__(self):
            return '<Node: %s>' % self.id


    _current = None

    def add_before_current(self, node_val):
        node = CircularDoubleLinkedList.Node(node_val)

        if self._current is None:
            node.next = node
            node.prev = node
            self._current = node
        else:
            self._current.prev.next = node
            node.prev = self._current.prev

            node.next = self._current
            self._current.prev = node

    def remove_node(self, node_val):
        logging.info('removing: %s', node_val)
        if self._current is None:
            raise ValueError()
        current = self._current
        while True:
            current = current.next
            if current.val == node_val:

                # If a single element
                if self._current.next is self._current:
                    self._current = None
                else:
                    current.prev.next = current.next
                    current.next.prev = current.prev

                    self._current = self._current.next
                current.next = current.prev = None
                break
            if current is self._current:
                raise AssertionError('Full circle')

    def __iter__(self):
        return self

    def next(self):
        if self._current is not None:
            self._current = self._current.next
        return self._current and self._current.val

    @property
    def current(self):
        if self._current is not None:
            return self._current.val
        else:
            return None

    def __len__(self):
        current = self._current
        if current is not None:
            res = 1
            current = current.next
            while current != self._current:
                current = current.next
                res += 1
        else:
            res = 0
        return res


class UserScheduler_(threading.Thread):
    _interval = 15

    def __init__(self):
        self._ioloop = ioloop.IOLoop.instance()
        self._must_pick_next_user = threading.Event()
        self._users = CircularDoubleLinkedList()
        self._log = get_class_logger(UserScheduler_)
        self._dispatcher = Dispatcher
        self._last_current = None
        self._last_time = 0
        return super(UserScheduler_, self).__init__()

    def run(self):
        UsersContainer.subscribe_all(self.callback)
        self._dispatcher.subscribe('new_current_meta', self._new_subscriber)

        last_current = self._users.current
        for new_current in self._users:
            self._last_time = time.time()
            if new_current != last_current:
                self._log.debug('new current: %s', new_current)
                if new_current is not None:
                    self._log.info('setting new current: %s', new_current)
                self._notify()
                control(0)
            last_current = new_current
            self._must_pick_next_user.wait(self._interval)
            self._must_pick_next_user.clear()

    def callback(self, args):
        self._log.debug('scheduler got event: %s', str(args))
        event = args[0]
        values = list(args[1:])

        user = values[0]
        if event == 'user added':
            self._users.add_before_current(user)
            if len(self._users) == 1:
                self._must_pick_next_user.set()
        elif event == 'user removed':
            must_pick_next = self._users.current == user
            try:
                self._users.remove_node(user)
            except ValueError:
                pass

            if must_pick_next:
                self._must_pick_next_user.set()

    def _new_subscriber(self, event):
        action, callback = event
        if action == 'add':
            self._notify([callback])

    def _notify(self, cbs=None):
        self._log.debug("notifying")

        if self._users.current is None:
            curr_user_id = None
        else:
            curr_user_id = self._users.current['id']


        def exec_in_ioloop():
            if cbs is None:
                if curr_user_id != self._last_current:
                    self._dispatcher.notify('new_current', (curr_user_id,
                                                            self._interval))
            else:
                for cb in cbs:
                    cb((curr_user_id,
                        self._interval - (time.time() - self._last_time)))
            self._last_current = curr_user_id

        self._ioloop.add_callback(exec_in_ioloop)

    def get_current_user(self):
        return self._users.current and self._users.current['id']

UserScheduler = UserScheduler_()

class MainHandler(web.RequestHandler):
    def get(self):
        names = UsersContainer.get_users()

        self.render("templates/index.html")

class User(object):
    def __init__(self, name=None, id_=None):
        self.name = name
        self.id = id(self) if id_ is None else id_
        self.active = False

    def as_dict(self):
        return {'id': self.id, 'name': self.name}

    def __str__(self):
        return '<User: %s %s (%s)>' % (self.name, self.active, self.id)
class UserWSHandler(WebSocketHandler):
    _user = None
    log = get_class_logger(WebSocketHandler)
    _dispatcher = Dispatcher

    def open(self):
        self._user = User()
        UsersContainer.subscribe_all(self._on_users_change)
        self._dispatcher.subscribe('new_current', self._on_current_user_change)
        self._dispatcher.subscribe('image_state_change',
                                   self._image_state_change)
        self._dispatcher.subscribe('pressed_state_change',
                                   self._on_pressed_state_change)
        self._dispatcher.subscribe('sensors-data',
                                   self._on_sensors_data)

        msg = {'event': 'your_id', 'values': [self._user.id]}
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)
        msg = {'event': 'sensors-list', 'values': BotHolder.interesting_sensors}
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)

    def _image_state_change(self, event):
        if event['event'] == 'new_img':
            msg = event
        else:
            raise NotImplementedError()
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)

    def _on_current_user_change(self, arg):
        new_id, period = arg
        msg = {'event': 'new_current', 'values': [new_id, period]}
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)

    def _set_name(self, new_name):
        old_name = self._user.name
        self._user.name = new_name
        if not self._user.active:
            UsersContainer.add_user(self._user)
            self._user.active = True
        else:
            UsersContainer.change_name(self._user, old_name, new_name)

    def _on_pressed_state_change(self, arg):
        msg = {'event': 'new_pressed_state', 'values': [arg]}
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)

    def on_message(self, message):
        self.log.debug('socket says: %s', message)
        try:
            message = urlparse.parse_qs(str(message))
        except Exception:
            raise
        self.log.debug('parsed message: %s', message)

        if not message:
            return
        try:
            if message['action'][0] == 'part':
                UsersContainer.remove_user(self._user)
                self._user.active = False
            elif message['action'][0] == 'name':
                self._set_name(message['value'][0])
            elif message['action'][0] == 'control':
                try:
                    value = int(message['value'][0])
                except ValueError:
                    return
                if UserScheduler.get_current_user() == self._user.id:
                    self._dispatcher.notify('pressed_state_change', value)
                    control(value)
        except KeyError:
            traceback.print_exc()

    def _on_users_change(self, args):
        event = args[0]
        values = list(args[1:])
        msg = {'event': event, 'values': values}
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)

    def _on_sensors_data(self, sensors):
        msg = {'event': 'sensors-data', 'values': [sensors]}
        self.log.debug('writing msg: %s', msg)
        self.write_message(msg)

    def on_close(self):
        UsersContainer.unsubscribe_all(self._on_users_change)
        self._dispatcher.unsubscribe_all(self._on_current_user_change)
        self._dispatcher.unsubscribe_all(self._image_state_change)
        self._dispatcher.unsubscribe_all(self._on_sensors_data)
        UsersContainer.remove_user(self._user)


class DevStaticFileHandler(web.StaticFileHandler):
    def get_cache_time(path, modified, mime_type):
        return -1


application = web.Application([
    (r"/", MainHandler),
    (r"/ws", UserWSHandler),
    web.URLSpec(r"/image", ImageHandler, name='image'),
    (r"/static/", DevStaticFileHandler,
     dict(path=settings['static_path'])),
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    UserScheduler.daemon = True
    UserScheduler.start()
    ioloop.IOLoop.instance().start()

