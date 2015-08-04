import pymongo

CONTEXT_ALREADY_EXISTS = 1
CONTEXT_NOT_FOUND = 2
CONTEXT_TYPE_INCORRECT = 3

SUCCESS = 0


class Apps(object):
    def __init__(self):
        self.select_ids = []
        self.update_ids = []
        self.context_set = {}

    def begin_query(self, app_id):
        return self.__begin_context(str(app_id), 'select')

    def begin_update(self, app_id):
        return self.__begin_context(str(app_id), 'update')

    def abort_query(self, context):
        return self.__remove_context(context)

    def abort_update(self, context):
        return self.__remove_context(context)

    def execute_query(self, context):
        obj = self.context_set[context].commit()
        self.__remove_context(context)
        return obj

    def execute_update(self, context):
        obj = self.context_set[context].commit()
        self.__remove_context(context)
        return obj

    def get_name(self, context):
        return self.__add_query_field(context, 'name')

    def get_category(self, context):
        return self.__add_query_field(context, 'category')

    def get_comment(self, context):
        return self.__add_query_field(context, 'comment')

    def update_name(self, context, new_name):
        check_result = self.__check_context(context, 'update')
        if check_result != SUCCESS:
            return check_result
        self.context_set[context].update_tables['name'] = new_name

    def update_category(self, context, new_category):
        check_result = self.__check_context(context, 'update')
        if check_result != SUCCESS:
            return check_result
        self.context_set[context].update_tables['category'] = new_category

    def update_comment(self, context, new_comment):
        check_result = self.__check_context(context, 'update')
        if check_result != SUCCESS:
            return check_result
        self.context_set[context].update_tables['comment'] = new_comment

    def get_apps(self, fields, conditions):
        pass

    def __begin_context(self, app_id, context_type):
        context = context_type + '_' + app_id
        if context_type == 'select':
            ids = self.select_ids
        elif context_type == 'update':
            ids = self.update_ids
        else:
            return CONTEXT_TYPE_INCORRECT

        if context in ids:
            return CONTEXT_ALREADY_EXISTS
        ids.append(context)

        self.context_set[context] = Context(app_id, context_type)
        return context

    def __remove_context(self, context):
        if context not in self.context_set:
            return CONTEXT_NOT_FOUND

        context_type = self.context_set[context].action
        del self.context_set[context]

        if context_type == 'select':
            ids = self.select_ids
        elif context_type == 'update':
            ids = self.update_ids
        else:
            return CONTEXT_TYPE_INCORRECT

        for i in range(len(ids)):
            if context == ids[i]:
                del ids[i]
                return

    def __add_query_field(self, context, field):
        if context not in self.select_ids:
            return CONTEXT_NOT_FOUND

        if field not in self.context_set[context].fields:
            self.context_set[context].fields.append(field)

        return SUCCESS

    def __add_query_filter(self, context, name, value):
        if name not in self.context_set[context].query_filter:
            self.context_set[context].query_filter[name] = value
        return SUCCESS

    def __check_context(self, context, action):
        if context not in self.context_set:
            return CONTEXT_NOT_FOUND

        if action != self.context_set[context].action:
            return CONTEXT_TYPE_INCORRECT
        return SUCCESS


class Context(object):
    ACTION_TYPES = ('select', 'update')

    def __init__(self, app_id, action):
        self.app_id = app_id
        self.action = action
        self.selector = {'app_id': app_id}
        self.fields = []
        self.update_tables = {}

    def commit(self):
        default_database = 'mongodb://127.0.0.1/apps'
        # default_database = 'mongodb://127.0.0.1:27017'
        mongodb = pymongo.MongoClient(default_database).apps
        apps = mongodb.apps
        if self.action == 'select':
            # fields = {}
            # for field in self.fields:
            #     fields[field] = 1
            document = apps.find_one(self.selector, self.fields)
            # data = Data()
            data = []
            for field in self.fields:
                if field in document:
                    # data.__setattr__(field, document[field])
                    data.append(document[field])
                # else:
                    # data.__setattr__(field, None)
            return data
        elif self.action == 'update':
            # update_field_value = {}
            # for field in self.update_tables:
            #     update_field_value[field] = self.update_tables[field]
            modifier = {'$set': self.update_tables}
            apps.update(self.selector, modifier, multi=False)
            return True
        else:
            pass


class Data(object):
    def __init__(self):
        pass

    def __setattr__(self, name, value):
        self.__dict__[name] = value
