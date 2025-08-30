import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# These values are the defaults from encryption.py
password = "default_medical_chatbot_key_2024"
salt = "medical_chatbot_salt".encode()

# This setup exactly matches the key derivation function in encryption.py
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)

# 1. Derive the raw key from the password
derived_key = kdf.derive(password.encode())

# 2. Encode the key in Base64 to get the final string, just like the application does
encryption_key = base64.urlsafe_b64encode(derived_key)

print("✅ Your Encryption Key is:")
print(encryption_key.decode())