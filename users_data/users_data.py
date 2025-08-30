import base64
from cryptography.fernet import Fernet

# --- PASTE YOUR VALUES HERE ---

# The secret key you obtained from the environment variable (Method 1).
# It must be a Base64-encoded string.
# If you are using the default password/salt (Method 2), you would need to
# run the key derivation part of the encryption.py script first to generate this key.
your_encryption_key_as_string = "9BgjwOejSIBSIVZGskeGwT_NJ9EfYA6RYI_b-m3j5lg="

# The encrypted data you copied from the database.
encrypted_data_from_db = 'Z0FBQUFBQm9udHF2ZXpQOFg5X2JMaWNvRFYweHVLRkFJUnFUakRUNVdsZF94LW9BTVRqUUE3U3h3TWZkcER2MFZRM2JsTmc3a21KaTBHODNSUmladnZ3bTlmSWVSMjNJWW84cnVBeHZYeHVXMHd6N1JpU1liVFVONnhULWV2RlZ4ZENGelVSRGFkaVg='

# --- DECRYPTION LOGIC ---

try:
    # Prepare the key and initialize Fernet
    key_bytes = your_encryption_key_as_string.encode()
    fernet = Fernet(key_bytes)

    # Decrypt the data (this reverses the steps in encryption.py)
    decoded_data = base64.urlsafe_b64decode(encrypted_data_from_db.encode())
    decrypted_bytes = fernet.decrypt(decoded_data)
    original_text = decrypted_bytes.decode()
    
    print("✅ Decryption Successful!")
    print(f"Original Data: {original_text}")

except Exception as e:
    print(f"❌ Decryption Failed: {e}")
    print("This could be due to an incorrect key or corrupted data.")