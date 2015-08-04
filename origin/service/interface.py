import argparse
import tornado.web

from apphandler import (
    RegisterHandler,
    UnRegisterHandler,
    UpdateHandler,
    QueryHandler
)
from common.constants import *
from zmq.eventloop import ioloop


def main():
    ioloop.install()
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', help='Bind interface')
    parser.set_defaults(interface=DEFAULT_INTERFACE)
    options = parser.parse_args()

    application = tornado.web.Application([
        (r'/apps/register', RegisterHandler),
        (r'/apps/unregister', UnRegisterHandler),
        (r'/apps/([0-9]+)', UpdateHandler),
        (r'/apps/query', QueryHandler)
    ])

    application.options = options
    address, port = options.interface.split(':')
    application.listen(port, address=address)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print 'Interrupted'

if __name__ == '__main__':
    main()