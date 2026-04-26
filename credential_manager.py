"""
Credential Manager Module
-------------------------
Handles secure storage and retrieval of user credentials.
Allows dynamic updates from frontend inputs.
"""

import json
import os
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CredentialManager")

CREDS_FILE = "creds.json"

class CredentialManager:
    """
    Manages user credentials for Upstox API.
    """
    
    def __init__(self, filepath=CREDS_FILE):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create empty creds file if it doesn't exist."""
        if not os.path.exists(self.filepath):
            default_structure = {
                "auth": {
                    "client_id": "",
                    "client_pass": "",
                    "client_pin": "",
                    "api_key": "",
                    "api_secret": "",
                    "redirect_uri": "https://www.upstox.com",
                    "code": "",
                    "access_token": "",
                    "last_updated": ""
                },
                "api": {
                    "headers": {},
                    "margin": {},
                    "positions": {},
                    "last_function": ""
                }
            }
            self.save_credentials(default_structure)
            logger.info(f"Created new credentials file at {self.filepath}")

    def load_credentials(self) -> Dict:
        """Load credentials from file."""
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}

    def save_credentials(self, creds: Dict):
        """Save credentials to file."""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(creds, f, indent=4)
            logger.info("Credentials saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def update_api_credentials(self, api_key: str, api_secret: str, client_id: str, redirect_uri: str = None):
        """
        Update API keys and client ID from frontend input.
        """
        creds = self.load_credentials()
        
        # Update fields
        creds["auth"]["api_key"] = api_key
        creds["auth"]["api_secret"] = api_secret
        creds["auth"]["client_id"] = client_id
        
        if redirect_uri:
            creds["auth"]["redirect_uri"] = redirect_uri
            
        self.save_credentials(creds)
        logger.info(f"Updated API credentials for user: {client_id}")
        return True

    def validate_credentials(self) -> bool:
        """Check if essential credentials are present."""
        creds = self.load_credentials()
        auth = creds.get("auth", {})
        
        required_fields = ["api_key", "api_secret", "client_id", "redirect_uri"]
        missing = [field for field in required_fields if not auth.get(field)]
        
        if missing:
            logger.warning(f"Missing credentials: {', '.join(missing)}")
            return False
        return True

if __name__ == "__main__":
    # Test
    cm = CredentialManager()
    print("Testing Credential Manager...")
    
    # Simulate frontend update
    cm.update_api_credentials(
        api_key="TEST_API_KEY",
        api_secret="TEST_API_SECRET",
        client_id="TEST_USER",
        redirect_uri="https://localhost:3000"
    )
    
    # Verify
    creds = cm.load_credentials()
    print(f"Loaded User: {creds['auth']['client_id']}")
    print(f"Valid: {cm.validate_credentials()}")
