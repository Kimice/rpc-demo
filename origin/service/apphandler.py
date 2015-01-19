import tornado.web
import tornado.gen
import logging
from appclient import *


class RequestHandler(tornado.web.RequestHandler):
    def prepare(self):
        try:
            self.message = json.loads(self.request.body)
        except ValueError:
            self.set_status(STATUS_BAD_REQUEST)
            self.finish()


class RegisterHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        id = str(self.message['id'])
        name = str(self.message['name'])
        app_client = AppClient(APP_INTERFACE, 10)
        try:
            yield app_client.register(id, name)
        except DataServiceError as e:
            logging.error(e)
            self.set_status(STATUS_CONFLICT)
        except TimeoutError as e:
            logging.error(e)
            self.set_status(STATUS_GATEWAY_TIMEOUT)
        else:
            self.set_status(STATUS_OK)


class UnRegisterHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        kw = str(self.message['kw'])
        value = str(self.message['value'])
        app_client = AppClient(APP_INTERFACE, 10)
        try:
            yield app_client.unregister(kw, value)
        except DataServiceError as e:
            logging.error(e)
            self.set_status(STATUS_NOT_FOUND)
        except TimeoutError as e:
            logging.error(e)
            self.set_status(STATUS_GATEWAY_TIMEOUT)
        else:
            self.set_status(STATUS_OK)


class UpdateHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, id):
        news = str(self.message['news'])
        story = str(self.message['story'])
        app_client = AppClient(APP_INTERFACE, 10)
        try:
            yield app_client.update(id, news, story)
        except DataServiceError as e:
            logging.error(e)
            self.set_status(STATUS_NOT_FOUND)
        except TimeoutError as e:
            logging.error(e)
            self.set_status(STATUS_GATEWAY_TIMEOUT)
        else:
            self.set_status(STATUS_OK)


class QueryHandler(RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        id = str(self.message['id'])
        app_client = AppClient(APP_INTERFACE, 10)
        try:
            result = yield app_client.query(id)
        except TimeoutError as e:
            logging.error(e)
            self.set_status(STATUS_GATEWAY_TIMEOUT)
        else:
            self.set_status(STATUS_OK)
        print result


if __name__ == '__main__':
    pass