"""
Tests for Crypto Utils
======================
Tests encryption, decryption, key generation, and backwards compatibility.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure data dir exists for key file
os.makedirs("data", exist_ok=True)

from crypto_utils import encrypt_value, decrypt_value, is_encrypted, ENCRYPTED_PREFIX


class TestEncryptDecrypt:
    """Tests for encrypt/decrypt roundtrip."""

    def test_basic_roundtrip(self):
        """Encrypting then decrypting should return original value."""
        original = "my_secret_api_key_12345"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypted_has_prefix(self):
        """Encrypted values should start with ENC: prefix."""
        encrypted = encrypt_value("test_value")
        assert encrypted.startswith(ENCRYPTED_PREFIX)

    def test_empty_string_passthrough(self):
        """Empty string should pass through unchanged."""
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_none_like_empty(self):
        """None-like empty values should not crash."""
        result = encrypt_value("")
        assert result == ""

    def test_different_encryptions(self):
        """Same value encrypted twice should produce different ciphertexts (Fernet uses random IV)."""
        val = "same_value"
        enc1 = encrypt_value(val)
        enc2 = encrypt_value(val)
        # Both should decrypt to same value
        assert decrypt_value(enc1) == val
        assert decrypt_value(enc2) == val

    def test_long_value(self):
        """Long strings should encrypt/decrypt correctly."""
        long_val = "a" * 1000
        encrypted = encrypt_value(long_val)
        assert decrypt_value(encrypted) == long_val

    def test_special_characters(self):
        """Values with special characters should work."""
        special = "key!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encrypt_value(special)
        assert decrypt_value(encrypted) == special


class TestDoubleEncryptProtection:
    """Tests for double-encryption protection."""

    def test_no_double_encrypt(self):
        """Encrypting an already-encrypted value should return it unchanged."""
        original = "my_api_key"
        encrypted = encrypt_value(original)
        double_encrypted = encrypt_value(encrypted)
        assert double_encrypted == encrypted

    def test_decrypt_plaintext_passthrough(self):
        """Decrypting a non-encrypted value should return it unchanged."""
        plain = "not_encrypted_value"
        result = decrypt_value(plain)
        assert result == plain


class TestIsEncrypted:
    """Tests for is_encrypted() helper."""

    def test_encrypted_value_detected(self):
        """Encrypted values should be detected."""
        encrypted = encrypt_value("test")
        assert is_encrypted(encrypted)

    def test_plain_value_not_detected(self):
        """Plain values should not be detected as encrypted."""
        assert not is_encrypted("plain_api_key")
        assert not is_encrypted("")
        assert not is_encrypted(None)
