class MyError(Exception):
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return self.value


class DataServiceError(MyError):
    pass


class TimeoutError(MyError):
    pass