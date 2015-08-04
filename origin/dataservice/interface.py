from datahandler import AppDataHandler
from common.constants import (
    APP_INTERFACE,
    ERROR_EXCEPTION,
    ERROR_SUCCESS
)
from common.message import (
    RequestFactory,
    Response,
    ResponseFactory
)
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import ZMQIOLoop


class DataService(object):

    def __init__(self, datahandler):
        self.datahandler = datahandler()

    def bind(self, interface):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(interface)
        stream = ZMQStream(socket)
        stream.on_recv_stream(self.dispatch)

    def dispatch(self, stream, message):
        request = RequestFactory().loads(message[0])
        response = Response()
        try:
            handler = getattr(self.datahandler, str.lower(request.method.encode('utf8')))
            response.result = handler(*request.params)
        except Exception as e:
            response.error = ERROR_EXCEPTION
            response.result = e
        else:
            response.error = ERROR_SUCCESS
        if not response.validate():
            response.error = ERROR_EXCEPTION
        stream.send(ResponseFactory().dumps(response))


def main():
    ds = DataService(AppDataHandler)
    ds.bind(APP_INTERFACE)
    try:
        ZMQIOLoop.instance().start()
    except KeyboardInterrupt:
        print 'Interrupted'

if __name__ == '__main__':
    main()