class Test(object):

    #TODO: do you guys want to support enum? I see there is a backport `pip install enum34`
    OPENED = 0
    CLOSED_SUCCESS = 1
    CLOSED_FAILURE = 2
    CLOSED_ERROR = 3
    def __init__(self, test_id, name):
        #TODO: where should test metadata be? **args, method for every param?
        self.test_id = test_id
        if name:
            self.name = name
        #create an open test in backslash

        #TODO:
        # What if I want to access an existing test? (create a Test class according to DB) - do I just provide
        # existing ID here and the code should figure it out? a different __init__ function?

    def add_comment(self, comment):
        pass

    def get_comments(self):
        pass

    def get_comment(self, comment_id):
        pass
    
    def attach_metadata(self, name, mime_type, data):
        pass

    def get_metadata(self, name):
        #TODO: yotam, why name here? we are in a single test object
        pass

    def delete_metadata(self, name):
        pass

    def delete(self):
        #delete the entry from backslash
        pass
    
    def end(self, status, duration=None):
        #find the open test in backslash and change it's status
        pass

    def success(self, duration=None):
        self.end(Test.CLOSED_SUCCESS, duration)

    def fail(self, duration=None):
        self.end(Test.CLOSED_FAILURE, duration)

    def error(self, duration=None):
        self.end(Test.CLOSED_ERROR, duration)

    def set_duration(self):
        #set duration
        pass

    def get_duration(self):
        #set duration
        pass
