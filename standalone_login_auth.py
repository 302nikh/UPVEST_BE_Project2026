# standalone_login_auth.py
"""
Standalone automated login & authentication module for Upstox API.
Handles: Selenium-based auto-login -> Auth code extraction -> Access token generation
Opens the logged-in Upstox dashboard after authentication and automatically handles popups.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pyotp
import requests
import json
from datetime import datetime
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ====================================================================
# 🔹 Function to handle popups on Upstox Pro dashboard
# ====================================================================
def handle_dashboard_popups(driver):
    """
    Automatically handles SEBI disclosure and navigation tour popups
    that appear after login in Upstox Pro.
    """
    try:
        logger.info("[POPUPS] Checking for SEBI disclosure popup...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Okay, I Understand')]"))
        ).click()
        logger.info("[POPUPS] ✅ Clicked 'Okay, I Understand' on SEBI popup.")
    except Exception:
        logger.info("[POPUPS] ℹ️ SEBI popup not found or already dismissed.")

    time.sleep(2)

    try:
        logger.info("[POPUPS] Checking for navigation tour popup...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Maybe later')]"))
        ).click()
        logger.info("[POPUPS] ✅ Clicked 'Maybe later' on navigation popup.")
    except Exception:
        logger.info("[POPUPS] ℹ️ Navigation popup not found or already closed.")


# ====================================================================
# 🔹 Your existing authentication flow (unchanged except one line)
# ====================================================================
def get_auth_code_via_selenium(client_id, client_pass_totp, client_pin, client_api_key):
    url = (
        "https://api-v2.upstox.com/login/authorization/dialog?"
        "response_type=code&client_id=" + client_api_key +
        "&redirect_uri=https://www.upvest.com"
    )

    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    logger.info("[AUTH] Starting Selenium-based login flow...")

    try:
        driver.get(url)

        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        logger.info("[AUTH] Step 1: Entering mobile number...")
        username_input_xpath = '//*[@id="mobileNum"]'
        username_input_element = driver.find_element(By.XPATH, username_input_xpath)
        username_input_element.clear()
        username_input_element.send_keys(client_id)

        logger.info("[AUTH] Step 2: Clicking Get OTP...")
        get_otp_button_xpath = '//*[@id="getOtp"]'
        driver.find_element(By.XPATH, get_otp_button_xpath).click()

        logger.info("[AUTH] Step 3: Entering TOTP...")
        client_pass = pyotp.TOTP(client_pass_totp).now()
        password_input_xpath = '//*[@id="otpNum"]'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, password_input_xpath))
        )
        driver.find_element(By.XPATH, password_input_xpath).send_keys(client_pass)

        logger.info("[AUTH] Step 4: Clicking Continue...")
        continue_button_xpath = '//*[@id="continueBtn"]'
        driver.find_element(By.XPATH, continue_button_xpath).click()

        logger.info("[AUTH] Step 5: Entering PIN...")
        pin_input_xpath = '//*[@id="pinCode"]'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, pin_input_xpath))
        )
        driver.find_element(By.XPATH, pin_input_xpath).send_keys(client_pin)

        original_url = driver.current_url

        logger.info("[AUTH] Step 6: Submitting PIN...")
        pin_continue_button_xpath = '//*[@id="pinContinueBtn"]'
        driver.find_element(By.XPATH, pin_continue_button_xpath).click()

        logger.info("[AUTH] Step 7: Waiting for redirect...")
        WebDriverWait(driver, 30).until(EC.url_changes(original_url))
        redirected_url = driver.current_url

        logger.info(f"[AUTH] Redirected URL: {redirected_url}")
        code_for_auth = redirected_url.split("?code=")[1]
        logger.info(f"[AUTH] ✓ Authorization code extracted: {code_for_auth[:15]}...")

        return code_for_auth, driver

    except Exception as e:
        logger.error(f"[AUTH] ✗ Selenium login failed: {e}")
        driver.quit()
        raise


def open_logged_in_dashboard(driver, access_token):
    """
    Opens Upstox Pro dashboard after login and handles any popups.
    """
    try:
        logger.info("\n[DASHBOARD] Opening Upstox Pro dashboard...")
        dashboard_url = "https://pro.upstox.com"
        driver.get(dashboard_url)

        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        logger.info("[DASHBOARD] ✓ Dashboard loaded successfully.")

        # NEW: Handle popups automatically
        handle_dashboard_popups(driver)

        logger.info("[DASHBOARD] Browser session active. Close manually when done.\n")

        while True:
            try:
                driver.current_window_handle
            except:
                logger.info("[DASHBOARD] Browser closed by user.")
                break

    except Exception as e:
        logger.error(f"[DASHBOARD] ✗ Failed to open dashboard: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass


def get_access_token_from_auth_code(auth_code, client_api_key, client_api_secret, redirect_uri):
    url = 'https://api.upstox.com/v2/login/authorization/token'
    headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'code': auth_code,
        'client_id': client_api_key,
        'client_secret': client_api_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    logger.info("[TOKEN] Requesting access token...")
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    token_data = response.json()
    logger.info(f"[TOKEN] ✓ Token received: {token_data.get('access_token')[:20]}...")
    return token_data.get('access_token'), token_data


def save_token_to_file(token_data, filename="access_token.json"):
    token_info = {
        'access_token': token_data.get('access_token'),
        'token_type': token_data.get('token_type'),
        'expires_in': token_data.get('expires_in'),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(filename, 'w') as f:
        json.dump(token_info, f, indent=4)
    logger.info(f"[FILE] ✓ Token saved to {filename}")
    return token_info


def load_token_from_file(filename="access_token.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            token_info = json.load(f)
        logger.info(f"[FILE] ✓ Token loaded from {filename}")
        return token_info
    logger.warning(f"[FILE] Token file not found: {filename}")
    return None


def perform_full_login_and_get_token(creds, save_token=True, open_dashboard=True):
    logger.info("\n" + "="*60)
    logger.info("UPSTOX AUTOMATED LOGIN & AUTHENTICATION")
    logger.info("="*60 + "\n")

    client_id = creds["auth"]["client_id"]
    client_pass_totp = creds["auth"]["client_pass"]
    client_pin = creds["auth"]["client_pin"]
    client_api_key = creds["auth"]["api_key"]
    client_api_secret = creds["auth"]["api_secret"]
    redirect_uri = creds["auth"]["redirect_uri"]

    driver = None
    try:
        logger.info("[STEP 1/4] Logging in...")
        auth_code, driver = get_auth_code_via_selenium(
            client_id, client_pass_totp, client_pin, client_api_key
        )

        logger.info("[STEP 2/4] Exchanging token...")
        access_token, token_data = get_access_token_from_auth_code(
            auth_code, client_api_key, client_api_secret, redirect_uri
        )

        if save_token:
            logger.info("[STEP 3/4] Saving token...")
            save_token_to_file(token_data)

        if open_dashboard and driver:
            logger.info("[STEP 4/4] Opening dashboard...")
            open_logged_in_dashboard(driver, access_token)

        logger.info("\n✓ AUTHENTICATION SUCCESSFUL\n")
        return access_token

    except Exception as e:
        logger.error(f"✗ AUTHENTICATION FAILED: {e}")
        if driver:
            driver.quit()
        raise


# ====================================================================
# Example usage
# ====================================================================
if __name__ == "__main__":
    from credential_manager import CredentialManager
    import sys

    # Initialize manager
    cm = CredentialManager()
    
    # Check if arguments provided (from frontend)
    # Usage: python standalone_login_auth.py <api_key> <api_secret> <client_id> <redirect_uri>
    if len(sys.argv) > 3:
        try:
            api_key = sys.argv[1]
            api_secret = sys.argv[2]
            client_id = sys.argv[3]
            redirect_uri = sys.argv[4] if len(sys.argv) > 4 else "https://www.upstox.com"
            
            print(f"Received credentials for {client_id} from frontend.")
            cm.update_api_credentials(api_key, api_secret, client_id, redirect_uri)
        except Exception as e:
            print(f"Error processing arguments: {e}")

    # Load and validate
    creds = cm.load_credentials()

    try:
        # Validate essential keys are present in creds
        if not creds.get("auth", {}).get("api_key") or not creds.get("auth", {}).get("api_secret"):
             print("❌ API Credentials missing. Please run with arguments or update creds.json")
             sys.exit(1)

        access_token = perform_full_login_and_get_token(creds, save_token=True, open_dashboard=True)
        print(f"\nAccess Token: {access_token}\n")
    except Exception as e:
        print(f"\nLogin failed: {e}\n")
