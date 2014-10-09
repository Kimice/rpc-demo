import zmq
import msgpack
from zmq.eventloop import ioloop, zmqstream
ioloop.install()


DEFAULT_INTERFACE = 'tcp://127.0.0.1:5556'


class Client(object):
    def __init__(self):
        self.stream = None
        self.result = None

    def connect(self, port):
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.connect(port)
        self.stream = zmqstream.ZMQStream(socket)

    def __getattr__(self, item):
        def wrapper(*args):
            request = [item]
            for param in args:
                request.append(param)
            return self._run(tuple(request))
        return wrapper

    def _run(self, request):
        def on_response(message):
            ioloop.ZMQIOLoop.instance().stop()
            response = msgpack.unpackb(message[0], use_list=False)
            if response[0] == 'OK':
                self.result = response[1]
            elif response[0] == 'ERR':
                raise Exception(response[2:])

        self.stream.send(msgpack.packb(request))
        self.stream.on_recv(on_response)
        ioloop.ZMQIOLoop.instance().start()
        return self.result

    def disconnect(self):
        self.stream.close()
