"""
Authentication Manager
----------------------
Handles user authentication, password hashing, and JWT token management.
"""

import bcrypt
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path


class AuthManager:
    """Manages user authentication and JWT tokens."""
    
    # JWT Secret Key - In production, use environment variable
    SECRET_KEY = "upvest_secret_key_2026_change_in_production"
    TOKEN_EXPIRY_DAYS = 7
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_token(user_id: int, email: str, name: str) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_id: User's database ID
            email: User's email
            name: User's full name
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'exp': datetime.utcnow() + timedelta(days=AuthManager.TOKEN_EXPIRY_DAYS),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, AuthManager.SECRET_KEY, algorithm='HS256')
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                AuthManager.SECRET_KEY, 
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        return True, ""


# Test the module
if __name__ == "__main__":
    print("Testing AuthManager...")
    
    # Test password hashing
    password = "TestPassword123"
    hashed = AuthManager.hash_password(password)
    print(f"[OK] Password hashed: {hashed[:50]}...")
    
    # Test password verification
    is_valid = AuthManager.verify_password(password, hashed)
    print(f"[OK] Password verification: {is_valid}")
    
    # Test wrong password
    is_valid = AuthManager.verify_password("WrongPassword", hashed)
    print(f"[OK] Wrong password rejected: {not is_valid}")
    
    # Test token generation
    token = AuthManager.generate_token(1, "test@example.com", "Test User")
    print(f"[OK] Token generated: {token[:50]}...")
    
    # Test token verification
    payload = AuthManager.verify_token(token)
    print(f"[OK] Token verified: {payload}")
    
    # Test email validation
    valid_email = AuthManager.validate_email("user@example.com")
    invalid_email = AuthManager.validate_email("invalid-email")
    print(f"[OK] Email validation: valid={valid_email}, invalid={not invalid_email}")
    
    # Test password strength
    weak_pass = AuthManager.validate_password_strength("weak")
    strong_pass = AuthManager.validate_password_strength("StrongPass123")
    print(f"[OK] Password strength: weak={not weak_pass[0]}, strong={strong_pass[0]}")
    
    print("\n[SUCCESS] All AuthManager tests passed!")
