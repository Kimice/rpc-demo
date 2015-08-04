import Queue
import zmq
from zmq.eventloop.zmqstream import ZMQStream


class StreamPool(object):

    def __init__(self, address, init_size):
        self.pool = Queue.Queue()
        self.address = address
        self.init_size = init_size
        for i in range(init_size):
            self.put_stream(self.create_stream(self.address))

    def put_stream(self, stream):
        self.pool.put(stream)

    def get_stream(self):
        if self.pool.empty():
            self.put_stream(self.create_stream(self.address))
        stream = self.pool.get()
        return stream

    @staticmethod
    def create_stream(address):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(address)
        stream = ZMQStream(socket)
        return stream

if __name__ == "__main__":
    StreamPool()

