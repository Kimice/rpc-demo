from pandorarpc.handler import Handler, async, stream
from pandorarpc.server import IOLoop, Server


class HelloRPC(Handler):
    def hello(self, category='test', *args, **kwargs):
        IOLoop.current().add_callback(test_method, 'test', 123, c='pandora')
        return "Hello from HelloRPC class, %s" % category

    @async
    def exception_test(self):
        raise ArithmeticError()

    @async
    def block_test(self):
        import time
        while True:
            time.sleep(1)

    @async
    def sub(self, i=1, j=2):
        self._result = i + j
        self.finish()

    def add(self, i, j=100, *args, **kwargs):
        self._result = i + j
        #http.fetch("http://friendfeed.com/", self._on_sum_done)

    @stream
    def progress(self, fr, to, step):
        return xrange(fr, to, step)

    def _on_sum_done(self):
        self.finish()


class HelloWorld(Handler):
    def hello(self, name):
        IOLoop.current().add_callback(test_method, 'test', 123, c='pandora')
        return "Hello from HelloWorld class, %s" % name

    @async
    def div(self, i=1, j=10):
        self._result = i / j
        self.finish()

    @async
    def mod(self, i, j=-1):
        self._result = i % j
        #http.fetch("http://friendfeed.com/", self._on_sum_done)

    def _on_sum_done(self):
        self.finish()


def test_method(a=1, b=2, c=3):
    print 'test_method was invoked. '
    print a, b, c


def main_test():
    test_endpoint1 = 'tcp://127.0.0.1:4242'
    s1 = Server(HelloRPC)
    s1.bind(test_endpoint1)

    test_endpoint2 = 'tcp://127.0.0.1:4243'
    s2 = Server(HelloWorld)
    s2.bind(test_endpoint2)

    IOLoop.instance().add_callback(test_method, 'test', 123, c='pandora')
    IOLoop.instance().add_callback(test_method, 'test', 123, c='pandora')
    IOLoop.instance().add_callback(test_method, 'test', 123, c='pandora')
    IOLoop.instance().run()

if __name__ == '__main__':
    try:
        main_test()
    except KeyboardInterrupt:
        print 'KeyboardInterrupt'
