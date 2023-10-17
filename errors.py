class DebugError(Exception):
    pass

class UserExistsError(FileExistsError):
    pass