class Connection(object):
    def __init__(address, authentication_information):
        pass

    def start_session(session_id):
        return Session(self, session_id)

    def close(self):
        pass

    def get_all_sessions(self):
        pass
    
    def get_sessions_by_user(self, user_id):
        pass

    def get_sessions_by_version(self, version):
        pass

    def get_sessions_by_environment(self, environment):
        pass

    def get_all_sessions_with_failures(self):
        pass

    def get_all_sessions_with_errors(self):
        pass

    def get_all_sessions_between_times(self, start_time, end_time):
        pass

    def get_last_session(self):
        pass
