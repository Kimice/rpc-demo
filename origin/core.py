import zmq
import msgpack
import traceback
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import ZMQIOLoop

from data import *


class Server(object):
    def __init__(self):
        self.data = Apps()

    def bind(self, port):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(port)
        stream = ZMQStream(socket)
        stream.on_recv_stream(self.dispatch)

    def dispatch(self, stream, message):
        request = msgpack.unpackb(message[0])
        handler = getattr(self.data, request[0])
        try:
            result = handler(*request[1:])
        except Exception as e:
            response = ('ERR', str(e.__class__), e.message, traceback.format_exc())
        else:
            response = ('OK', result)
        stream.send(msgpack.packb(response))

    @staticmethod
    def run():
        try:
            ZMQIOLoop.instance().start()
        except KeyboardInterrupt:
            print 'Interrupted'


class Client(object):
    def __init__(self):
        self.stream = None
        self.result = None

    def connect(self, port):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(port)
        self.stream = ZMQStream(socket)

    def __getattr__(self, item):
        def wrapper(*args):
            request = [item]
            for param in args:
                request.append(param)
            return self._run(tuple(request))
        return wrapper

    def _run(self, request):
        def on_response(message):
            response = msgpack.unpackb(message[0], use_list=False)
            if response[0] == 'OK':
                self.result = response[1]
            elif response[0] == 'ERR':
                raise Exception(response[2])
            ZMQIOLoop.instance().stop()

        self.stream.send(msgpack.packb(request))
        self.stream.on_recv(on_response)
        ZMQIOLoop.instance().start()
        return self.result

    def disconnect(self):
        self.stream.close()
