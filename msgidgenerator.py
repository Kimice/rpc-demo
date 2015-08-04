import uuid
import random


class MsgIdGenerator(object):
    _instance = None

    def __init__(self):
        self._reset_msgid()

    @property
    def _msg_id_base(self):
        return self.__dict__['_msg_id_base']

    @_msg_id_base.setter
    def _msg_id_base(self, value):
        self.__dict__['_msg_id_base'] = value

    @property
    def _msg_id_counter(self):
        return self.__dict__['_msg_id_counter']

    @_msg_id_counter.setter
    def _msg_id_counter(self, value):
        self.__dict__['_msg_id_counter'] = value

    @property
    def _msg_id_counter_stop(self):
        return self.__dict__['_msg_id_counter_stop']

    @_msg_id_counter_stop.setter
    def _msg_id_counter_stop(self, value):
        self.__dict__['_msg_id_counter_stop'] = value

    @staticmethod
    def get_instance():
        if MsgIdGenerator._instance is None:
            MsgIdGenerator._instance = MsgIdGenerator()
        return MsgIdGenerator._instance

    def _reset_msgid(self):
        self._msg_id_base = str(uuid.uuid4())[8:]
        self._msg_id_counter = random.randrange(0, 2**32)
        self._msg_id_counter_stop = random.randrange(self._msg_id_counter, 2**32)

    def new_msgid(self):
        if self._msg_id_counter >= self._msg_id_counter_stop:
            self._reset_msgid()
        else:
            self._msg_id_counter = (self._msg_id_counter + 1)
        return '{0:08x}{1}'.format(self._msg_id_counter, self._msg_id_base)
