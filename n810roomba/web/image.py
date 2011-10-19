import re
import logging
from datetime import timedelta

from tornado import ioloop, web
from tornado.curl_httpclient import CurlAsyncHTTPClient as AsyncHTTPClient

from n810roomba.web.dispatcher import Dispatcher


MJPEG_SOURCE = 'http://192.168.1.14:8080/videofeed'
CLIENT_RETRY_INTERVAL = 5
CLIENT_RETRY_TIMEDELTA = timedelta(seconds=CLIENT_RETRY_INTERVAL)
content_type_pattern = re.compile(r'Content-Type: ([^;]+);boundary=(\S*)\s*')


class ImageGrabber_(object):
    _clients = []
    _new_clients = []
    _meta_clients = []
    _working = False
    _headers = []

    __streaming = False

    _boundary = None
    _kill_http = False

    log = logging.getLogger(__name__ + '.ImageGrabber')

    def __init__(self):
        self._dispatcher = Dispatcher
        self._dispatcher.subscribe('image_data_meta', self._new_subscriber)

    def _new_subscriber(self, event):
        action, callback = event
        if action == 'add':
            self.subscribe(callback)
        elif action == 'del':
            self.unsubscribe(callback)

    def subscribe(self, handler):
        self._new_clients.append(handler)
        self.log.debug('client joined, now %d clients and %d new clients' % (
                len(self._clients), len(self._new_clients)))
        self.maybe_run()

    def unsubscribe(self, handler):
        try:
            self._clients.remove(handler)
        except ValueError:
            self._new_clients.remove(handler)
        if not self._clients:
            self._kill_http = True
            self.http = None
            #print 'stopped http client'
        self.log.debug('client left, now %d clients and %d new clients' % (
                len(self._clients), len(self._new_clients)))

    def maybe_run(self):
        if self._working:
            return

        # If had some clients from previous streaming session make them new.
        self._new_clients.extend(self._clients)
        self._clients = []

        if not self._clients + self._new_clients:
            self._working = False
            return

        self._headers = []
        self.http = AsyncHTTPClient(max_clients=1)
        self.http.fetch(MJPEG_SOURCE, self.on_request_done,
                        streaming_callback=self.on_chunk,
                        header_callback=self.on_header, request_timeout=0,
                        connect_timeout=1)
        self._working = True
        self.log.info('starting http client')

    def on_header(self, header):
        #print 'got header: %s' % header.strip()
        if header.startswith('HTTP/') or not header.strip():
            self._streaming = True
            return
        self._headers.append(header)
        matches = content_type_pattern.match(header)
        if matches:
            self._boundary = matches.group(2)
            #print 'got boundary: %s' % self._boundary

    def on_chunk(self, chunk):

        # No more clients left.
        if self._kill_http:
            self._kill_http = False
            return 1337

        for handler in self._clients:
            handler.on_image(chunk)

        if self._new_clients:
            try:
                frame_start = chunk.index(self._boundary)
            except ValueError:
                return

            for handler in self._new_clients:
                handler.on_headers(self._headers)
                handler.on_image(chunk[frame_start:])

                self._clients.append(handler)

        self._new_clients = []

    def on_request_done(self, response):
        self._working = False

        if response.error:
            if response.error.code == 599:
                self.log.error('Error opening source: %s', str(response.error))
            else:
                self.log.warning('source image finished')

        self._streaming = False

        ioloop.IOLoop.instance().add_timeout(CLIENT_RETRY_TIMEDELTA,
                                             self.maybe_run)
        return

        #for handler in self._clients:
        #    # Service unavailable
        #    handler.drop_client()

    def _get_streaming(self):
        return self.__streaming
    def _set_streaming(self, val):
        self.__streaming = val
        if val:
            src = '/image'
            msg = ''
        else:
            src = 'http://placekitten.com/640/480'
            msg = 'Image source not available'

        msg = {'event': 'new_img',
               'values': [src],
               'msg': msg}
        self._dispatcher.notify('image_state_change', msg)
    _streaming = property(_get_streaming, _set_streaming)


ImageGrabber = ImageGrabber_()

class ImageHandler(web.RequestHandler):
    log = logging.getLogger(__name__ + '.ImageHandler')
    _dispatcher = Dispatcher

    @web.asynchronous
    def get(self):
        ImageGrabber.subscribe(self)

    def on_headers(self, headers):
        for h in headers:
            print 'handler got header: %s' % h.strip()
            k, v = h.strip().split(': ', 1)
            self.set_header(k, v)

        self.flush()

    def on_image(self, chunk):
        if not self.request.connection.stream.closed():
            self.write(chunk)
            self.flush()
        else:
            self.log.debug('client droped')
            ImageGrabber.unsubscribe(self)
            #self.finish()

    def on_end(self):
        self.finish()
        ImageGrabber.unsubscribe(self)
