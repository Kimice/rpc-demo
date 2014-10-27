import msgpack
import zmq as zmq
import errno
from msgidgenerator import MsgIdGenerator


class RpcEvent(object):
    __slots__ = ['_name', '_args', '_header']

    def __init__(self, name, args, msgid, header=None):
        self._name = name
        self._args = args
        if header is None:
            self._header = {
                'message_id': msgid,
                'v': 3
            }
        else:
            self._header = header

    @property
    def header(self):
        return self._header

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        self._name = v

    @property
    def args(self):
        return self._args

    def pack(self):
        return msgpack.Packer().pack((self._header, self._name, self._args))

    @staticmethod
    def unpack(blob):
        unpacker = msgpack.Unpacker()
        unpacker.feed(blob)
        unpacked_msg = unpacker.unpack()

        try:
            (header, name, args) = unpacked_msg
        except Exception as e:
            raise Exception('invalid msg format "{0}": {1}'.format(
                unpacked_msg, e))

        if not isinstance(header, dict):
            header = {}

        return RpcEvent(name, args, None, header)

    def __str__(self, ignore_args=False):
        if ignore_args:
            args = '[...]'
        else:
            args = self._args
            try:
                args = '<<{0}>>'.format(str(self.unpack(self._args)))
            except:
                pass
        return '{0} {1} {2}'.format(self._name, self._header, args)


class Events(object):
    def __init__(self, zmq_socket_type=zmq.ROUTER):
        self._zmq_socket_type = zmq_socket_type
        self._msgid_generator = MsgIdGenerator.get_instance()
        self._socket = zmq.Context().socket(zmq_socket_type)

    def poll(self, timeout=1):
        events = self._socket.poll(timeout)
        return events & zmq.POLLIN == zmq.POLLIN

    def __del__(self):
        try:
            if not self._socket.closed:
                self.close()
        except AttributeError:
            pass

    def close(self):
        self._socket.close()

    def connect(self, endpoint):
        self._socket.connect(endpoint)

    def bind(self, endpoint):
        self._socket.bind(endpoint)

    def create_event(self, name, args, xheader={}):
        event = RpcEvent(name, args, msgid=self._msgid_generator.new_msgid())
        for k, v in xheader.items():
            if k == 'zmqid':
                continue
            event.header[k] = v
        return event

    def emit_event(self, event, identity=None):
        if identity is not None:
            parts = list(identity)
            parts.extend(['', event.pack()])
        elif self._zmq_socket_type in (zmq.DEALER, zmq.ROUTER):
            parts = ('', event.pack())
        else:
            parts = (event.pack(),)

        for i in xrange(len(parts) - 1):
            try:
                self.send(parts[i], flags=zmq.SNDMORE)
            except:
                if i == 0:
                    return
                self._socket.send(parts[i], flags=zmq.SNDMORE)
        self.send(parts[-1])

    def emit(self, name, args, xheader={}):
        event = self.create_event(name, args, xheader)
        identity = xheader.get('zmqid', None)
        return self.emit_event(event, identity)

    def send(self, data, flags=0, copy=True, track=False):
        if flags & zmq.NOBLOCK != zmq.NOBLOCK:
            flags |= zmq.NOBLOCK
        while True:
            try:
                msg = self._socket.send(data, flags, copy, track)
                return msg
            except zmq.ZMQError, e:
                if e.errno not in (zmq.EAGAIN, errno.EINTR):
                    raise

    def recv(self):
        parts = []
        while True:
            try:
                if self.poll(1):
                    part = self._socket.recv(zmq.NOBLOCK, True, False)
            except zmq.ZMQError, e:
                if e.errno not in (zmq.EAGAIN, errno.EINTR):
                    raise
            except:
                if len(parts) == 0:
                    break
            parts.append(part)
            if not self._socket.getsockopt(zmq.RCVMORE):
                break

        if parts is None:
            return None
        if len(parts) == 1:
            identity = None
            blob = parts[0]
        else:
            identity = parts[0:-2]
            blob = parts[-1]
        event = RpcEvent.unpack(blob)
        if identity is not None:
            event.header['zmqid'] = identity
        return event

    def setsockopt(self, *args):
        return self._socket.setsockopt(*args)

    @property
    def msgid_generator(self):
        return self._msgid_generator

    @property
    def socket(self):
        return self._socket
