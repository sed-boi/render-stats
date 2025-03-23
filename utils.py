import secrets
import string

def get_access_key():
    # Generate a secure 16-character alphanumeric key.
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))
