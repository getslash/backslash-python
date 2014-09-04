from test import Test


class Session(object):
    def __init__(self, connection, _id, name=None):
        self._connection = connection
        self._id = _id
        if name:
            self.name = name
        #create session entry in backslash

    #TODO: is it needed?
    def create_test(self, test_id, name=None):
        return Test(self, test_id, name)

    def start(self):
        # put in start time of session
        #TODO: is it needed? does sessions have a start and end? or is session a timeless object (can always add tests to it?)
        pass

    def end(self):
        #put in end time of session
        #TODO: is it needed? does sessions have a start and end or is session a timeless object (can always add tests to it?)
        pass

    def set_version(self, version):
        self.version = version
        #transmit it to DB
        pass

    def get_version(self):
        #TODO: not sure I like it, but it's an option: "caching" in the python
        if self.version:
            return self.version
        else:
            #get value from DB
            pass

    def set_user(self, userID):
        self.userID = userID
        #transmit it to DB
        pass

    def get_userID(self):
        #TODO: not sure I like it, but it's an option: "caching" in the python
        if self.userID:
            return self.userID
        else:
            #get value from DB
            pass

    def set_environment(self, environment):
        self.environment = environment
        #transmit it to DB

    def get_environment(self):
        #TODO: not sure I like it, but it's an option: "caching" in the python
        if self.environment:
            return self.environment
        else:
            #get value from DB
            pass

    def attach_metadata(self, name, mime_type, data):
        pass

    def get_metadata(self, name):
        pass

    def delete_metadata(self, name):
        pass

    def add_comment(self, markdown):
        pass

    def get_comments(self):
        pass

    def get_all_tests(self):
        pass
    
    def get_tests_by(self):
        pass

    def get_results_count(self):
        #TODO: return a tuple (pass, fail, error)? seperate method for each number?
        pass

    def delete(self):
        #delete the entry from backslash
        pass



