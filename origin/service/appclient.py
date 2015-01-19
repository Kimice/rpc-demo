import datetime
import tornado.gen
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

    @tornado.gen.coroutine
    def register(self, id, name):
        request = RegisterRequest()
        request.append(id)
        request.append(name)
        yield self.perform(request)

    @tornado.gen.coroutine
    def unregister(self, kw, value):
        request = UnRegisterRequest()
        request.append(kw)
        request.append(value)
        yield self.perform(request)

    @tornado.gen.coroutine
    def update(self, id, news, story):
        request = UpdateRequest()
        request.append(id)
        request.append(news)
        request.append(story)
        yield self.perform(request)

    @tornado.gen.coroutine
    def query(self, id):
        request = QueryRequest()
        request.append(id)
        response = yield self.perform(request)
        raise tornado.gen.Return(response.result)

    def perform(self, request):
        def on_timeout():
            io_loop.remove_timeout(to)
            self.pool.put_stream(stream)
            raise TimeoutError("timeout")

        def on_response(message):
            io_loop.remove_timeout(to)
            self.pool.put_stream(stream)
            response = ResponseFactory().loads(message[0])
            if response.error == ERROR_EXCEPTION:
                raise response.result
            future.set_result(response)

        future = Future()
        stream = self.pool.get_stream()
        stream.send(RequestFactory().dumps(request))
        io_loop = ZMQIOLoop().instance()
        wait_time = datetime.timedelta(seconds=2)
        to = io_loop.add_timeout(wait_time, on_timeout)
        stream.on_recv(on_response)
        return future


if __name__ == "__main__":
    pass