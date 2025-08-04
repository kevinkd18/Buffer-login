from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cookie file path
COOKIE_FILE = "buffer_cookies.pkl"

def take_screenshot(driver, filename):
    """Take a screenshot and save it"""
    try:
        driver.save_screenshot(filename)
        print(f"📸 Screenshot saved: {filename}")
    except Exception as e:
        print(f"⚠️ Failed to take screenshot: {str(e)}")

def save_cookies(driver):
    """Save current cookies to file"""
    with open(COOKIE_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print("💾 Session cookies saved successfully!")

def load_cookies(driver):
    """Load cookies from file if exists"""
    if not os.path.exists(COOKIE_FILE):
        return False
    
    try:
        # First visit the domain to set cookies
        driver.get("https://buffer.com")
        
        # Load cookies
        with open(COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            driver.add_cookie(cookie)
        
        print("🍪 Session cookies loaded successfully!")
        return True
    except Exception as e:
        print(f"⚠️ Failed to load cookies: {str(e)}")
        return False

def setup_chrome():
    options = Options()
    # Set headless mode based on environment variable (default to True)
    headless = os.getenv('HEADLESS', 'True').lower() == 'true'
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')  # Often needed for headless mode
    options.add_argument('--window-size=1920,1080')  # Set consistent window size
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def check_session_validity(driver):
    """Check if the current session is valid by visiting dashboard"""
    try:
        driver.get("https://publish.buffer.com/all-channels")
        time.sleep(3)
        
        if "publish.buffer.com" in driver.current_url:
            print("✅ Session is valid!")
            return True
        else:
            print("⚠️ Session is invalid or expired")
            return False
    except Exception as e:
        print(f"⚠️ Session validation failed: {str(e)}")
        return False

def login_with_credentials(driver, EMAIL, PASSWORD):
    """Perform login using credentials"""
    try:
        print("Opening Buffer login page...")
        driver.get("https://login.buffer.com/login")
        
        # Handle potential cookie consent
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
            ).click()
            print("Accepted cookies")
        except:
            print("No cookie consent found")
        
        # Improved CAPTCHA handling
        try:
            print("Looking for human verification...")
            # Wait for iframe to load
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title,'reCAPTCHA')]"))
            )
            driver.switch_to.frame(iframe)
            
            # Click checkbox inside iframe
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='recaptcha-checkbox-checkmark']"))
            )
            checkbox.click()
            print("Clicked CAPTCHA checkbox")
            
            # Switch back to main content
            driver.switch_to.default_content()
            time.sleep(3)  # Allow time for verification
        except Exception as e:
            print(f"CAPTCHA handling failed: {str(e)}")
            driver.switch_to.default_content()  # Ensure we're back to main content
        
        print("Entering email...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        email_field.clear()
        email_field.send_keys(EMAIL)
        
        print("Entering password...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        print("Clicking login...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        
        print("Waiting for login to complete...")
        # Wait for either dashboard URL or error message
        try:
            WebDriverWait(driver, 20).until(
                EC.or_(
                    EC.url_contains("publish.buffer.com"),
                    EC.url_contains("buffer.com/app"),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Invalid')]"))
                )
            )
        except:
            print("Login process timed out")
        
        # Check login status
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        print(f"Page title: {driver.title}")
        
        # Updated success conditions
        if "publish.buffer.com" in current_url or "buffer.com/app" in current_url:
            print("✅ Login successful!")
            save_cookies(driver)
            return True
        else:
            # Check for error messages
            try:
                error_element = driver.find_element(By.XPATH, "//*[contains(text(),'Invalid') or contains(text(),'incorrect')]")
                error = error_element.text
                print(f"❌ Login failed: {error}")
            except:
                print("⚠ Login status unclear")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False

def main():
    try:
        # Get credentials from environment variables
        EMAIL = os.getenv('EMAIL')
        PASSWORD = os.getenv('PASSWORD')
        
        if not EMAIL or not PASSWORD:
            raise ValueError("EMAIL and PASSWORD must be set in .env file")
        
        print("Starting Chrome...")
        driver = setup_chrome()
        
        # First try to load existing session cookies
        session_valid = False
        if load_cookies(driver):
            # Check if session is still valid
            if check_session_validity(driver):
                print("🚀 Session restored successfully!")
                session_valid = True
            else:
                print("⚠️ Session expired. Proceeding with credential login...")
        
        # If session is invalid or doesn't exist, login with credentials
        if not session_valid:
            if login_with_credentials(driver, EMAIL, PASSWORD):
                print("🚀 Login successful! Session is active.")
            else:
                print("❌ Login failed. Please check credentials.")
                return None
        
        print("✅ Session established and cookies saved!")
        return driver
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if 'driver' in locals():
            take_screenshot(driver, "login_exception.png")
        return None

if __name__ == "__main__":
    driver = main()
    
    if driver:
        print("\n🚀 Session established successfully! You can now run newpost.py")
        input("Press Enter to close the browser...")
        driver.quit()
