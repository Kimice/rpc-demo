import time

import zmq

from rpc.events import Events


class ChannelMultiplexer():
    def __init__(self, zmq_socket_type=zmq.ROUTER):
        self._events = Events(zmq_socket_type)
        self._channels = {}

    @property
    def socket(self):
        return self._events.socket

    @property
    def channels(self):
        return self._channels

    def bind(self, endpoint):
        self._events.bind(endpoint)

    def close(self):
        self._events.close()

    def poll(self, poll_timeout=1):
        return self._events.poll(poll_timeout)

    def recv(self):
        return self._events.recv()

    def create_event(self, name, args, xheader={}):
        return self._events.create_event(name, args, xheader)

    def emit_event(self, event, identity=None):
        return self._events.emit_event(event, identity)

    def emit(self, name, args, xheader={}):
        return self._events.emit(name, args, xheader)

    def channel(self, freq=5, from_event=None):
        return Channel(self, freq, from_event)


class Channel():
    def __init__(self, multiplexer, freq=5, from_event=None):
        self._multiplexer = multiplexer
        self._channel_id = None
        self._zmqid = None
        self._heartbeat_freq = freq
        self._remote_last_hb = None
        self._answered_last_hb = None
        self._lost_remote = False
        self.rpc_handler = None
        if from_event is not None:
            self._channel_id = from_event.header['message_id']
            self._zmqid = from_event.header.get('zmqid', None)
            self._multiplexer.channels[self._channel_id] = self

    def remote_last_hb(self, value):
        self._remote_last_hb = value

    def __del__(self):
        self.close()

    def close(self):
        if self._channel_id is not None:
            del self._multiplexer.channels[self._channel_id]
            self._channel_id = None

    def create_event(self, name, args, xheader={}):
        event = self._multiplexer.create_event(name, args, xheader)
        if self._channel_id is None:
            self._channel_id = event.header['message_id']
            self._multiplexer.channels[self._channel_id] = self
        else:
            event.header['response_to'] = self._channel_id
        return event

    def emit(self, name, args, xheader={}):
        event = self.create_event(name, args, xheader)
        self._multiplexer.emit_event(event, self._zmqid)

    def emit_event(self, event):
        self._multiplexer.emit_event(event, self._zmqid)

    def finish_stream(self, resp_stream):
        for result in iter(resp_stream.result):
            self.emit('STREAM', result, {})
        self.emit('STREAM_DONE', None, {})

    def finish(self, result):
        self.emit('OK', (result,), {})

    def on_idle(self):
        if self._remote_last_hb is not None:
            if time.time() > self._remote_last_hb + self._heartbeat_freq * 2:
                self._lost_remote = True
                self.close()
            else:
                if self._answered_last_hb is None or \
                        self._answered_last_hb < self._remote_last_hb:
                    self._answered_last_hb = time.time()
                    self.emit('_zpc_hb', (0,))
                else:
                    pass