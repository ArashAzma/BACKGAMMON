from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    public_key = private_key.public_key()
    
    return private_key, public_key

def save_key(key, filename, is_private=False):
    if is_private:
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    else:
        pem = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    with open(filename, 'wb') as f:
        f.write(pem)
        
def load_private_key(filename):
    with open(filename, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )
    return private_key

def load_public_key(filename):
    with open(filename, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())
    return public_key        

node1_private, node1_public = generate_keys()
node2_private, node2_public = generate_keys()
node3_private, node3_public = generate_keys()

save_key(node1_private, 'keys/node1_private_key.pem', is_private=True)
save_key(node1_public, 'keys/node1_public_key.pem')
save_key(node2_private, 'keys/node2_private_key.pem', is_private=True)
save_key(node2_public, 'keys/node2_public_key.pem')
save_key(node3_private, 'keys/node3_private_key.pem', is_private=True)
save_key(node3_public, 'keys/node3_public_key.pem')