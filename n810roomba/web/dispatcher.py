from collections import defaultdict
import logging


log = logging.getLogger('dispatcher')


class Dispatcher_(object):
    _subscriptions = defaultdict(list)

    def subscribe(self, event, callback):
        log.debug('subscribe %s: %s', event, callback)
        self._subscriptions[event].append(callback)
        self.notify(event + '_meta', ('add', callback))

    def unsubscribe(self, event, callback):
        log.debug('unsubscribe %s: %s', event, callback)
        self._subscriptions[event].remove(callback)

    def unsubscribe_all(self, cb):
        for k, v in self._subscriptions.iteritems():
            if cb in v:
                self.unsubscribe(k, cb)

    def notify(self, event, arg):
        log.debug('notify %s: %s', event, arg)
        for cb in self._subscriptions[event]:
            cb(arg)

Dispatcher = Dispatcher_()
