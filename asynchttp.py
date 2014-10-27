import pycurl


class AsyncHTTPResult():
    OPERATION_SUCCEED = 0
    GENERAL_FAILURE = -1

    def __init__(self, code=GENERAL_FAILURE):
        self.code = code


class AsyncHTTPClients():
    def __init__(self):
        self._curl_multi = pycurl.CurlMulti()
        self._handle_curls = []
        self._wait_curls = []

    def get_fdset(self):
        return self._curl_multi.fdset()

    def add(self, curl):
        self._wait_curls.append(curl)

    def run_once(self):
        self._add()
        ret = self._curl_multi.select(1.0)
        if ret == -1:
            return

        self._curl_multi.perform()
        result = self._curl_multi.info_read()
        for i in result[1]:
            http_result = AsyncHTTPResult(AsyncHTTPResult.OPERATION_SUCCEED)
            http_resp = HTTPResponse(code=i.getinfo(i.HTTP_CODE),
                                     headers=None,
                                     body_buffer=i.body_buf)
            self.run_callback(i, http_result, http_resp)
            self._remove(i)
        for i in result[2]:
            http_result = AsyncHTTPResult()
            self.run_callback(i[0], http_result)
            self._remove(i[0])

    @staticmethod
    def run_callback(curl, http_result, http_resp=None):
        try:
            curl.callback(http_result, http_resp)
        except Exception as e:
            print e

    def _add(self):
        wait_curls = self._wait_curls[:]
        self._wait_curls = []
        for req in wait_curls:
            self._handle_curls.append(req)
            self._curl_multi.add_handle(req)

    def _remove(self, req):
        req.close()
        self._handle_curls.remove(req)
        self._curl_multi.remove_handle(req)


class AsyncHTTPClient():
    def __init__(self, io_loop=None):
        from server import IOLoop
        self._io_loop = io_loop or IOLoop.current()

    def fetch(self, curl):
        self._io_loop.async_http_clients.add(curl)


class HTTPResponse(object):
    def __init__(self, code, headers=None, body_buffer=None, error=None):
        self.code = code
        self.headers = headers
        self.body_buffer = body_buffer
        self._body = None
        if error is None:
            if self.code < 200 or self.code >= 300:
                self.error = HTTPError(self.code)
            else:
                self.error = None
        else:
            self.error = error

    def _get_body(self):
        if self.body_buffer is None:
            return None
        elif self._body is None:
            self._body = self.body_buffer.getvalue()

        return self._body

    body = property(_get_body)


class HTTPError(Exception):
    def __init__(self, code, message=None, response=None):
        self.code = code
        self.response = response
        Exception.__init__(self, "HTTP %d: %s" % (self.code, message))
