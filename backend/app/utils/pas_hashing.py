from argon2 import PasswordHasher


def get_hash_pass(password)->str:
    return PasswordHasher().hash(password)

def match_password(hash_pas, pas)->None:
    PasswordHasher().verify(hash_pas, pas)