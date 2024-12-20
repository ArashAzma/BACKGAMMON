from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

def generate_key():
    return os.urandom(32)

def encrypt_message(key, message):
    iv = os.urandom(16)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message) + padder.finalize()
    
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    return iv + encrypted_data

def decrypt_message(key, encrypted_message):
    iv = encrypted_message[:16]
    ciphertext = encrypted_message[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    try:
        return unpadder.update(decrypted_padded) + unpadder.finalize()
    except ValueError as e:
        raise ValueError("Decryption failed - invalid padding") from e
    
def load_or_generate_keys():
    key_file = "relay_keys.bin"
    
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            keys_data = f.read()
            return [keys_data[i:i+32] for i in range(0, len(keys_data), 32)]
    else:
        keys = [generate_key() for _ in range(3)]
        with open(key_file, "wb") as f:
            for key in keys:
                f.write(key)
        return keys

RELAY_KEYS = load_or_generate_keys()