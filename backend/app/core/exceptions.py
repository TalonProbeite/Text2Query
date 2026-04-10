class UserAlreadyExists(Exception): pass
class UserNotFound(Exception): pass
class InvalidPassword(Exception): pass
class JWTTokenGenerateError(Exception): pass
class JWTTokenDecodeError(Exception): pass
class UserBannedError(Exception): pass
class NotSqlPromt(Exception):pass
class DBConnectionError(Exception):pass
class DBQueryError(Exception):pass