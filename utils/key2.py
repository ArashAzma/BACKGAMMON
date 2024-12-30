from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import os
from base64 import b64encode, b64decode



def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt(message, public_key):
    encrypted_message = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )
    return encrypted_message

def decrypt(encrypted_message, private_key):
    plaintext = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )
    return plaintext.decode()
def decrypt2(encrypted_message, private_key):
    plaintext = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )
    return plaintext

def serialize_private_key(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def split_and_encrypt_key(private_key_bytes, chunk_size, encryption_key):
    chunks = [private_key_bytes[i:i+chunk_size] for i in range(0, len(private_key_bytes), chunk_size)]
    encrypted_chunks = []
    
    for chunk in chunks:
        if len(chunk) < chunk_size:
            chunk = chunk + b'\0' * (chunk_size - len(chunk))  # Pad if necessary
        try:
            encrypted_chunks.append(encrypt(chunk, encryption_key))
        except ValueError as e:
            print(f"Encryption failed for chunk of size {len(chunk)}. Error: {e}")
            continue  
    
    return encrypted_chunks

def split_and_encrypt_key2(private_key_bytes, chunk_size, encryption_key):
    chunks = [private_key_bytes[i:i+chunk_size] for i in range(0, len(private_key_bytes), chunk_size)]
    encrypted_chunks = []
    
    for chunk in chunks:
        if len(chunk) < chunk_size:
            chunk = chunk
        try:
            print(f"Encrypting chunk of size {len(chunk)}")
            x = encrypt(chunk, encryption_key)
            print(f"Encrypting chunk of size {len(x)}")
            encrypted_chunks.append(encrypt(chunk, encryption_key))
        except ValueError as e:
            print(f"Encryption failed for chunk of size {len(chunk)}. Error: {e}")
            continue  
    
    return encrypted_chunks


def reassemble_key(encrypted_chunks):
    decrypted_bytes = bytearray()
    
    for encrypted_chunk in encrypted_chunks:
        decrypted_bytes.extend(encrypted_chunk)
    
    try:
        null_index = decrypted_bytes.index(b'\0')
        return bytes(decrypted_bytes[:null_index])
    except ValueError:
        return bytes(decrypted_bytes)

def decrypt_and_reassemble_key(encrypted_chunks, decryption_key):
    decrypted_bytes = bytearray()
    
    for encrypted_chunk in encrypted_chunks:
        decrypted_chunk = decrypt(encrypted_chunk, decryption_key)
        if isinstance(decrypted_chunk, str):
            decrypted_chunk = decrypted_chunk.encode('utf-8')
        
        decrypted_bytes.extend(decrypted_chunk)
    
    try:
        null_index = decrypted_bytes.index(b'\0')
        return bytes(decrypted_bytes[:null_index])
    except ValueError:
        return bytes(decrypted_bytes)

def load_private_key(private_key_str):
    private_key_bytes = private_key_str.encode()  
    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=default_backend(),
    )
    return private_key

def remove_padding(data):
    # Remove trailing zeros
    return data.rstrip(b'\x00')

def decrypt_final_layer(encrypted_chunks, private_key):
    # Get the RSA key size
    key_size = private_key.key_size // 8  # Convert bits to bytes
    
    # First ensure all chunks are the correct size
    if len(encrypted_chunks) == 0:
        return None
        
    decrypted_parts = []
    try:
        # Process each chunk and decrypt
        combined = remove_padding(encrypted_chunks)
        if len(combined) != key_size:
            # Pad with zeros if needed
            combined = combined.ljust(key_size, b'\x00')
        
        decrypted = decrypt(combined, private_key)
        return decrypted
        
    except Exception as e:
        print(f"Decryption error: {e}")
        return None