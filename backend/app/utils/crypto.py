"""
app/utils/crypto.py
===================
Cryptographic utilities for API keys and device auth tokens.
"""
import hashlib
import secrets

def get_hash(secret: str) -> str:
    """Generate SHA-256 hash of a secret string."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()

def generate_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_hex(length // 2)
