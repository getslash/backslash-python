class Session(object):
    def __init__(self, connection, name, _id = None):
        self._connection = connection
        self._name = name
        if not _id:
            self._session_id = connection.create_session()
        else:
            self.connection.asset_session_id_exists(_id)
            self._session_id = _id
        
    def start_test(self, name):
        return Test(self, name)

    def set_metadata(self, name, mime_type, data):
        pass

    def get_metadata(self, name):
        pass

    def add_comment(self, markdown):
        pass

    def get_comments(self):
        pass

    def get_all_tests(self):
        pass
    
    def get_tests_by(self):
        pass

    def delete(self):
        pass
    
    def end(self):
        pass



