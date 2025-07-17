from cryptography.fernet import Fernet

# Generate a key and save it securely. This should be done once and the key stored safely.
# key = Fernet.generate_key()
# print(key.decode())

import os
from cryptography.fernet import Fernet

# Load key from environment variable or fallback to hardcoded key
FERNET_KEY = os.environ.get('ENCRYPTION_KEY')
if FERNET_KEY:
    FERNET_KEY = FERNET_KEY.encode()
else:
    FERNET_KEY = b'your-generated-fernet-key-here'

fernet = Fernet(FERNET_KEY)

def encrypt(data: str) -> str:
    """Encrypt a string."""
    return fernet.encrypt(data.encode()).decode()

def decrypt(token: str) -> str:
    """Decrypt a string."""
    return fernet.decrypt(token.encode()).decode()