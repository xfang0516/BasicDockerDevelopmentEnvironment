# generate_keys.py
from nacl.signing import SigningKey

# Create a key pair.
sk = SigningKey.generate()
# Print the private key in hexadecimal format.
print("private key:", sk.encode().hex())
# Print the public key in hexadecimal format.
print("public key:", sk.verify_key.encode().hex())