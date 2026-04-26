import time
import requests
import urllib.parse

def get_auth_code(client_id, redirect_uri):
    """
    Get Upstox authorization code.
    Since we don't have the original GUI automation script, we will redirect 
    to the CLI or use the standalone login auth logic which is more robust.
    """
    print(f"\n[ACTION REQUIRED] Please authorize the Upstox Login")
    print(f"URL: https://api-v2.upstox.com/login/authorization/dialog?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}")
    print("\nAfter logging in, you will be redirected to a URL that looks like:")
    print(f"{redirect_uri}?code=YOUR_AUTH_CODE")
    
    code = input("\nEnter the YOUR_AUTH_CODE part here: ").strip()
    return code

def upstox_auth_code(creds):
    """
    Main entry point called by upstox.py
    """
    client_id = creds["auth"]["api_key"]
    redirect_uri = creds["auth"]["redirect_uri"]
    
    # Check if we should use the new standalone auth system instead
    try:
        from standalone_login_auth import run_auth_server
        print("[AUTH] Starting automated token server...")
        token_info = run_auth_server()
        if token_info and 'code' in token_info:
            return token_info['code']
    except ImportError:
        pass
        
    return get_auth_code(client_id, redirect_uri)

if __name__ == "__main__":
    # Test
    creds = {
        "auth": {
            "api_key": "test_client_id",
            "redirect_uri": "http://127.0.0.1:5000"
        }
    }
    print(upstox_auth_code(creds))
