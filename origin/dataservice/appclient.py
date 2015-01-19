import datetime
from tornado.concurrent import Future
from zmq.eventloop.ioloop import ZMQIOLoop
from common.message import *
from common.constants import *
from streampool import *
from dataerror import *


def singleton(cls):
    instances = {}

    def _singleton(args, kw):
        if cls not in instances:
            instances[cls] = cls(args, kw)
        return instances[cls]
    return _singleton


@singleton
class AppClient(object):

    def __init__(self, address, init_size):
        self.pool = StreamPool(address, init_size)

    def perform(self, request):
        def on_timeout():
            io_loop.remove_timeout(to)
            future.set_result(response)
            raise TimeoutError("timeout")

        def on_response(message):
            io_loop.remove_timeout(to)
            if not future.done():
                response = ResponseFactory().loads(message[0])
                future.set_result(response)
                if response.error == ERROR_EXCEPTION:
                    raise response.result
            self.pool.put_stream(stream)

        future = Future()
        response = Response()
        stream = self.pool.get_stream()
        stream.send(RequestFactory().dumps(request))
        io_loop = ZMQIOLoop().instance()
        wait_time = datetime.timedelta(seconds=2)
        to = io_loop.add_timeout(wait_time, on_timeout)
        stream.on_recv(on_response)
        return future


if __name__ == "__main__":
    pass