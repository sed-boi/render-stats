# utils.py
import random

def get_access_key():
    # Generate and return a random 4-digit key as a string.
    return str(random.randint(1000, 9999))
