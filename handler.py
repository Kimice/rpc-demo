import functools
import inspect


def async(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self._auto_finish = False
        result = method(self, *args, **kwargs)
        return result
    wrapper._rpc_args = inspect.getargspec(method)
    return wrapper


def stream(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        return RespStream(method(self, *args, **kwargs))
    wrapper._rpc_args = inspect.getargspec(method)
    return wrapper


class RespStream():
    def __init__(self, result):
        self.result = result


class Handler(object):
    def __init__(self, server, channel):
        self.server = server
        self.channel = channel
        self.method_to_execute = None
        self._auto_finish = True
        self._result = None
        self._error = None

    def _when_complete(self, result, callback):
        try:
            self._result = result
            callback()
        except:
            pass

    def _execute_method(self, *args, **kwargs):
        self._when_complete(self.method_to_execute(*args, **kwargs),
                            self._execute_finish)

    def _execute_finish(self):
        if self._auto_finish:
            self.finish()

    def finish(self):
        if self.channel:
            if self._error:
                self.channel.finish(self._error)
            else:
                if isinstance(self._result, RespStream):
                    self.channel.finish_steam(self._result)
                else:
                    self.channel.finish(self._result)
            self.channel.close()

    def set_result(self, result):
        self._result = result

    def set_error(self, error):
        self._error = error
