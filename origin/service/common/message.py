import re
import json
from constants import (
    METHOD_UPDATE,
    METHOD_QUERY,
    METHOD_UNREGISTER,
    METHOD_REGISTER
)


class Message(object):
    def validate(self):
        return True


class Request(Message):
    def __init__(self):
        self.method = None
        self.params = list()
        
    def validate(self):
        if self.method is None:
            return False
        return True

    def append(self, value):
        self.params.append(value)
        
    def get(self, index):
        return self.params[index]


class RegisterRequest(Request):
    def __init__(self):
        super(RegisterRequest, self).__init__()
        self.method = METHOD_REGISTER
        
    def validate(self):
        if not re.match(r'^\d{4}$', self.params[0]):
            return False
        if not re.match(r'^\w{1,128}$', self.params[1]):
            return False
        return True


class UnRegisterRequest(Request):
    def __init__(self):
        super(UnRegisterRequest, self).__init__()
        self.method = METHOD_UNREGISTER


class UpdateRequest(Request):
    def __init__(self):
        super(UpdateRequest, self).__init__()
        self.method = METHOD_UPDATE


class QueryRequest(Request):
    def __init__(self):
        super(QueryRequest, self).__init__()
        self.method = METHOD_QUERY


class RequestFactory(object):
    @staticmethod
    def loads(document):
        document = json.loads(document)
        method = document['method']
        request = globals()[method+'Request']()
        request.__dict__ = document
        return request

    @staticmethod
    def dumps(request):
        return json.dumps(request.__dict__)


class Response(Message):
    def __init__(self):
        self.error = None
        self.result = dict()

    def validate(self):
        if self.error is None:
            return False
        return True
    
    def set_param(self, key, value):
        self.result[key] = value

    def get_param(self, key, *default):
        return self.result.get(key, *default)


def object2dict(obj):
    d = dict()
    d['__class__'] = obj.__class__.__name__
    d['__module__'] = obj.__module__
    d.update(obj.__dict__)
    return d


def dict2object(d):
    if'__class__' in d:
        class_name = d.pop('__class__')
        module_name = d.pop('__module__')
        module = __import__(module_name)
        class_ = getattr(module, class_name)
        args = dict((key.encode('ascii'), value) for key, value in d.items())
        inst = class_(**args)
    else:
        inst = d
    return inst


class ResponseFactory(object):
    @staticmethod
    def loads(document):
        document = json.loads(document, object_hook=dict2object)
        response = Response()
        response.__dict__ = document
        return response

    @staticmethod
    def dumps(response):
        return json.dumps(response.__dict__, default=object2dict)