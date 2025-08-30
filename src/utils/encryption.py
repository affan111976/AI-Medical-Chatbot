import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or create a new one"""
        # Try to get key from environment variable
        key_string = os.getenv("ENCRYPTION_KEY")
        
        if key_string:
            try:
                return key_string.encode()
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Create new key from password or generate random
        password = os.getenv("ENCRYPTION_PASSWORD", "default_medical_chatbot_key_2024")
        salt = os.getenv("ENCRYPTION_SALT", "medical_chatbot_salt").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Save key to environment for future use (in production, use secure key management)
        logger.info("Generated new encryption key. Consider setting ENCRYPTION_KEY in environment.")
        
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return ""
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return ""
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ""  # Return empty string instead of raising error
    
    def is_encrypted(self, data: str) -> bool:
        """Check if data appears to be encrypted"""
        try:
            # Try to decode as base64 and decrypt
            decoded_data = base64.urlsafe_b64decode(data.encode())
            self.fernet.decrypt(decoded_data)
            return True
        except:
            return False

# Global encryption instance
encryption_manager = EncryptionManager()

def encrypt_data(data: str) -> str:
    """Convenience function to encrypt data"""
    return encryption_manager.encrypt(data)

def decrypt_data(encrypted_data: str) -> str:
    """Convenience function to decrypt data"""
    return encryption_manager.decrypt(encrypted_data)

def is_data_encrypted(data: str) -> bool:
    """Convenience function to check if data is encrypted"""
    return encryption_manager.is_encrypted(data)