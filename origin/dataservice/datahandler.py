import pymongo
from common.message import *
from dataerror import *


def singleton(cls):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return _singleton


@singleton
class AppDataHandler(object):
    def __init__(self):
        mongodb = pymongo.MongoClient(DEFAULT_LIBRARY)
        database = mongodb.get_default_database()
        self.collection = database[DEFAULT_COLLECTION]

    def register(self, id, name):
        if self.collection.find_one({'_id': id}):
            raise DataServiceError("id already existed")
        elif self.collection.find_one({'name': name}):
            raise DataServiceError("name already existed")
        else:
            self.collection.insert({'_id': id, 'name': name})

    def unregister(self, kw, value):
        if kw == 'id':
            if not self.collection.find_and_modify({'_id': value}, remove=True):
                raise DataServiceError("id not found")
        if kw == 'name':
            if not self.collection.find_and_modify({'name': value}, remove=True):
                raise DataServiceError("name not found")

    def update(self, id, news, story):
        if not self.collection.find_and_modify(
                {'_id': id},
                {'$set': {'news': news, 'story': story}}):
            raise DataServiceError("app not found")

    def query(self, id):
        app = self.collection.find_one({'_id': id})
        return app
