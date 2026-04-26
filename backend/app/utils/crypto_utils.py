from cryptography.fernet import Fernet

from app.core.config import settings


class CryptoUtils:
    def __init__(self,  key = settings.crypto.key):
        self.key = key
        self.cipher = Fernet(self.key.encode())

    def encrypt_password(self, password: str) -> str:

        encrypted_bytes = self.cipher.encrypt(password.encode())
        return encrypted_bytes.decode()

    def decrypt_password(self, encrypted_password: str) -> str:

        decrypted_bytes = self.cipher.decrypt(encrypted_password.encode())
        return decrypted_bytes.decode()
