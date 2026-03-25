class UserAlreadyExists(Exception): pass
class UserNotFound(Exception): pass
class InvalidPassword(Exception): pass
class JWTTokenGenerateError(Exception): pass
class JWTTokenDecodeError(Exception): pass
class UserBannedError(Exception): pass