import random

def mod_exp(base, exp, mod):
    """Efficient modular exponentiation."""
    result = 1
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp //= 2
    return result

def generate_keys(prime):
    """Generate public and private keys."""
    g = 2  
    d = random.randint(2, prime - 2)  # Private key
    e = mod_exp(g, d, prime)   # Public key
    return (e, g, prime), d

def encrypt(message, public_key):
    """Encrypt a message."""
    e, g, p = public_key
    return mod_exp(message, e, p)

def decrypt(ciphertext, private_key, prime):
    """Decrypt a ciphertext."""
    return mod_exp(ciphertext, private_key, prime)