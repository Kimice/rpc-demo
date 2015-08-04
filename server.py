import inspect
import time
import threading
import functools
from zmq.sugar.poll import select
from channel import ChannelMultiplexer
from asynchttp import AsyncHTTPClients


class IOLoop(object):
    _instance_lock = threading.Lock()
    _current = threading.local()

    @staticmethod
    def instance():
        if not hasattr(IOLoop, "_instance"):
            with IOLoop._instance_lock:
                if not hasattr(IOLoop, "_instance"):
                    IOLoop._instance = IOLoop()
        return IOLoop._instance

    @staticmethod
    def initialized():
        return hasattr(IOLoop, "_instance")

    def install(self):
        assert not IOLoop.initialized()
        Server._instance = self

    @staticmethod
    def current():
        current = getattr(IOLoop._current, "instance", None)
        if current is None:
            return IOLoop.instance()
        return current

    def make_current(self):
        IOLoop._current.instance = self

    @staticmethod
    def clear_current():
        IOLoop._current.instance = None

    def __init__(self):
        self._callbacks = []
        self._callback_lock = threading.Lock()
        self._servers = []
        self.async_http_clients = AsyncHTTPClients()

    def add_server(self, server):
        self._servers.append(server)

    def add_callback(self, callback, *args, **kwargs):
        with self._callback_lock:
            self._callbacks.append(functools.partial(callback, *args, **kwargs))

    def _run_callback(self, callback):
        try:
            callback()
        except:
            self.handle_callback_exception(callback)

    def handle_callback_exception(self, callback):
        pass

    def run(self):
        IOLoop._current.instance = self
        while True:
            poll_timeout = 0.1
            with self._callback_lock:
                callbacks = self._callbacks
                self._callbacks = []
            for callback in callbacks:
                self._run_callback(callback)

            if self._callbacks:
                poll_timeout = 0

            sockets = []
            for server in self._servers:
                sockets.append(server.socket)

            for socket in self.async_http_clients.get_fd_set()[0]:
                sockets.append(socket)

            if len(sockets) > 0:
                rwx_list = select(sockets, [], sockets, poll_timeout)
                for server in self._servers:
                    if server.socket in rwx_list[0]:
                        server.run()
                    elif server.socket in rwx_list[2]:
                        print 'Error: ZMQ socket error.'  # TODO: Log this error?
                    else:
                        pass

                self.async_http_clients.run_once()

                for server in self._servers:
                    server.on_idle()


class Server(object):
    def __init__(self, rpc_handler):
        self.builtin_methods = ['_rpc_inspect',
                                '_rpc_name',
                                '_rpc_ping',
                                '_rpc_list',
                                '_rpc_help',
                                '_rpc_args']
        self._multiplexer = ChannelMultiplexer()
        self._rpc_handler = rpc_handler
        self._rpc_name = getattr(rpc_handler, '__name__', None)
        self._rpc_methods = self._filter_methods(Server, self, rpc_handler)
        self._inject_builtins()
        for (k, method) in self._rpc_methods.items():
            self._rpc_methods[k] = method

    @staticmethod
    def _filter_methods(cls, self, methods):
        if hasattr(methods, '__getitem__'):
            return methods
        server_methods = set(getattr(self, k) for k in dir(cls) if not
                k.startswith('_'))
        return dict((k, getattr(methods, k))
                    for k in dir(methods)
                    if callable(getattr(methods, k))
                       and not k.startswith('_')
                       and getattr(methods, k) not in server_methods
                    )

    @staticmethod
    def _format_args_spec(args_spec, r=None):
        if args_spec:
            r = [dict(name=name) for name in args_spec[0]]
            default_values = args_spec[3]
            if default_values is not None:
                for arg, def_val in zip(reversed(r), reversed(default_values)):
                    arg['default'] = def_val
        return r

    def _rpc_inspect(self):
        methods = dict((m, f) for m, f in self._rpc_methods.items()
                       if not m.startswith('_'))
        detailed_methods = dict((m,
            dict(args=self._format_args_spec(self.rpc_args(f)),
                 doc=self._rpc_doc(f)))
            for (m, f) in methods.items())
        return {'name': self._rpc_name,
                'methods': detailed_methods}

    @staticmethod
    def _rpc_doc(method):
        if method.__doc__ is None:
            return None
        return inspect.cleandoc(method.__doc__)

    @staticmethod
    def rpc_args(method):
        try:
            args_spec = method.rpc_args
        except AttributeError:
            try:
                args_spec = inspect.getargspec(method)
            except TypeError:
                try:
                    args_spec = inspect.getargspec(method.__call__)
                except (AttributeError, TypeError):
                    args_spec = None
        return args_spec

    def _inject_builtins(self):
        self._rpc_methods['_rpc_inspect'] = self._rpc_inspect
        self._rpc_methods['_rpc_name'] = lambda: self._rpc_name
        self._rpc_methods['_rpc_ping'] = lambda: ['pong', self._rpc_name]
        self._rpc_methods['_rpc_list'] = \
            lambda: [m for m in self._rpc_methods if not m.startswith('_')]
        self._rpc_methods['_rpc_help'] = \
            lambda m: self._rpc_doc(self._rpc_methods[m])
        self._rpc_methods['_rpc_args'] = \
            lambda m: self._format_args_spec(self.rpc_args(self._rpc_methods[m]))

    @property
    def socket(self):
        return self._multiplexer.socket

    def bind(self, endpoint):
        self._multiplexer.bind(endpoint)
        IOLoop.instance().add_server(self)

    def close(self):
        self._multiplexer.close()

    def run(self):
        event = self._multiplexer.recv()
        if event is not None:
            channel_id = event.header.get('response_to', None)
            if channel_id is None:
                channel_id = event.header['message_id']
            if channel_id in self._multiplexer.channels:
                channel = self._multiplexer.channels[channel_id]
            else:
                channel = self._multiplexer.channel(5, event)

            if event.name == '_zpc_hb':
                channel.remote_last_hb(time.time())
            else:
                try:
                    if channel.rpc_handler is None:
                        channel.rpc_handler = self._rpc_handler(self, channel)
                    rpc_handler = channel.rpc_handler
                    if event.name in self.builtin_methods:
                        method = self._rpc_methods.get(event.name, None)
                    else:
                        method = getattr(rpc_handler, event.name, None)
                    if method is None:
                        raise NameError(event.name)
                    else:
                        rpc_handler.method_to_execute = method
                        rpc_handler.execute_method(*event.args)
                except Exception as e:
                    channel.finish_exception(str(e))
                    channel.close()

    def on_idle(self):
        for channel_id in self._multiplexer.channels.keys():
            self._multiplexer.channels[channel_id].on_idle()
