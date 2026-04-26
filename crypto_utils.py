"""
Crypto Utilities
================
Provides Fernet symmetric encryption for sensitive data like API keys.
The encryption key is stored locally in data/.encryption_key.

Usage:
    from crypto_utils import encrypt_value, decrypt_value
    
    encrypted = encrypt_value("my_api_secret")
    decrypted = decrypt_value(encrypted)
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet

KEY_FILE = Path("data/.encryption_key")

# Prefix to identify encrypted values
ENCRYPTED_PREFIX = "ENC:"


def _ensure_key_exists():
    """Generate encryption key if it doesn't exist."""
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        print("[CRYPTO] Generated new encryption key")


def _load_key() -> bytes:
    """Load encryption key from file."""
    _ensure_key_exists()
    with open(KEY_FILE, 'rb') as f:
        return f.read()


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a plaintext string.
    
    Args:
        plaintext: The string to encrypt
        
    Returns:
        Encrypted string with 'ENC:' prefix
    """
    if not plaintext:
        return plaintext
    
    # Don't double-encrypt
    if plaintext.startswith(ENCRYPTED_PREFIX):
        return plaintext
    
    key = _load_key()
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode('utf-8'))
    return ENCRYPTED_PREFIX + encrypted.decode('utf-8')


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt an encrypted string.
    
    Args:
        ciphertext: The encrypted string (with 'ENC:' prefix)
        
    Returns:
        Decrypted plaintext string
    """
    if not ciphertext:
        return ciphertext
    
    # If not encrypted, return as-is (backwards compatible)
    if not ciphertext.startswith(ENCRYPTED_PREFIX):
        return ciphertext
    
    key = _load_key()
    f = Fernet(key)
    encrypted_data = ciphertext[len(ENCRYPTED_PREFIX):]
    decrypted = f.decrypt(encrypted_data.encode('utf-8'))
    return decrypted.decode('utf-8')


def is_encrypted(value: str) -> bool:
    """Check if a value is already encrypted."""
    return value.startswith(ENCRYPTED_PREFIX) if value else False


if __name__ == "__main__":
    # Quick self-test
    print("=" * 40)
    print("Crypto Utils Self-Test")
    print("=" * 40)
    
    test_secret = "my_super_secret_api_key_12345"
    print(f"Original:  {test_secret}")
    
    encrypted = encrypt_value(test_secret)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = decrypt_value(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert decrypted == test_secret, "Decryption failed!"
    
    # Test double-encrypt protection
    double_enc = encrypt_value(encrypted)
    assert double_enc == encrypted, "Double encryption protection failed!"
    
    # Test backwards compatibility (plain text passes through)
    plain = decrypt_value("not_encrypted_value")
    assert plain == "not_encrypted_value", "Backwards compatibility failed!"
    
    print("\n[OK] All tests passed!")
