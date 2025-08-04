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
import glob

# Cookie file path
COOKIE_FILE = "buffer_cookies.pkl"
VIDEO_DIR = "/workspaces/codespaces-blank/videos"

def take_screenshot(driver, filename):
    """Take a screenshot and save it"""
    try:
        driver.save_screenshot(filename)
        print(f"📸 Screenshot saved: {filename}")
    except Exception as e:
        print(f"⚠️ Failed to take screenshot: {str(e)}")

def load_cookies(driver):
    """Load cookies from file if exists"""
    if not os.path.exists(COOKIE_FILE):
        return False
    
    try:
        # First visit the root domain to set cookies
        driver.get("https://buffer.com")
        time.sleep(2)  # Wait for page to load
        
        # Load cookies
        with open(COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)
        
        # Add cookies one by one, handling domain mismatches
        skipped = 0
        current_domain = "buffer.com"
        for cookie in cookies:
            try:
                # If the cookie's domain is a parent domain (like .buffer.com), it should work
                if 'domain' in cookie and cookie['domain'] == '.buffer.com':
                    # Set domain to current domain without the leading dot
                    cookie['domain'] = current_domain
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"Skipping cookie (domain: {cookie.get('domain', 'N/A')}): {str(e)}")
                skipped += 1
                continue
        
        if skipped > 0:
            print(f"⚠️ Skipped {skipped} cookies due to domain mismatch")
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

def click_new_post(driver):
    """Click on the New Post button"""
    try:
        print("Navigating to all channels page...")
        driver.get("https://publish.buffer.com/all-channels")
        time.sleep(3)
        
        print("Looking for New Post button...")
        # Try multiple selectors for the New Post button
        selectors = [
            "/html/body/div[1]/div[1]/main/div[1]/header/div[1]/div/button[2]",  # Provided XPath
            "//button[contains(text(), 'New Post')]",  # Text-based selector
            "//button[.//span[contains(text(), 'New Post')]]",  # Span inside button
            "//button[contains(@class, 'new-post')]",  # Class-based selector
            "//button[.//*[name()='svg']]"  # Button with SVG icon
        ]
        
        new_post_button = None
        for selector in selectors:
            try:
                new_post_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"Found New Post button using selector: {selector}")
                break
            except:
                continue
        
        if not new_post_button:
            print("❌ Could not find New Post button with any selector")
            take_screenshot(driver, "new_post_button_not_found.png")
            return False
        
        print("Clicking New Post button...")
        new_post_button.click()
        
        print("Waiting for New Post dialog to open...")
        time.sleep(3)
        
        # Verify the dialog opened by checking for elements that should appear
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'composer') or contains(text(), 'Create a new post')]"))
            )
            print("✅ New Post dialog opened successfully!")
            return True
        except:
            print("⚠️ New Post dialog might not have opened properly")
            take_screenshot(driver, "new_post_dialog_check.png")
            return True  # Still return true as we clicked the button
            
    except Exception as e:
        print(f"❌ Error clicking New Post button: {str(e)}")
        take_screenshot(driver, "new_post_error.png")
        return False

def upload_video(driver):
    """Upload a video from the videos directory"""
    try:
        # Get the first video file in the directory
        video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
        if not video_files:
            print(f"❌ No video files found in {VIDEO_DIR}")
            return False
        
        video_path = video_files[0]
        print(f"Found video: {video_path}")
        
        # Find the file input element (it's usually hidden)
        print("Looking for file input element...")
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        
        # Send the file path to the input element
        print("Uploading video...")
        file_input.send_keys(video_path)
        
        # Wait for upload to complete (look for progress indicator or completion message)
        print("Waiting for upload to complete...")
        time.sleep(5)  # Initial wait
        
        # Check for upload completion indicators
        try:
            # Look for a progress bar that disappears or a completion message
            WebDriverWait(driver, 120).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'upload-progress')]"))
            )
            print("✅ Video upload completed!")
        except:
            # Alternative: Check for a success message or thumbnail
            try:
                WebDriverWait(driver, 120).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'media-preview') or contains(text(), 'Upload complete')]"))
                )
                print("✅ Video upload completed!")
            except:
                print("⚠️ Could not confirm upload completion, but proceeding anyway")
        
        take_screenshot(driver, "video_uploaded.png")
        return True
        
    except Exception as e:
        print(f"❌ Error uploading video: {str(e)}")
        take_screenshot(driver, "video_upload_error.png")
        return False

def type_content(driver):
    """Type the content in the text area"""
    try:
        print("Looking for text area...")
        text_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[2]/section[3]/div/div/div/div[1]/div[1]/div[1]/div/div"))
        )
        
        print("Typing content...")
        text_area.click()
        text_area.clear()
        text_area.send_keys("#viral #Reels")
        
        print("✅ Content typed successfully!")
        take_screenshot(driver, "content_typed.png")
        return True
        
    except Exception as e:
        print(f"❌ Error typing content: {str(e)}")
        take_screenshot(driver, "content_type_error.png")
        return False

def click_customize_button(driver):
    """Click the 'Customize for each network' button"""
    try:
        print("Looking for Customize button...")
        customize_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[2]/section[4]/div/button"))
        )
        
        print("Clicking Customize button...")
        customize_button.click()
        
        print("✅ Customize button clicked successfully!")
        take_screenshot(driver, "customize_clicked.png")
        return True
        
    except Exception as e:
        print(f"❌ Error clicking Customize button: {str(e)}")
        take_screenshot(driver, "customize_error.png")
        return False

def click_second_text_area(driver):
    """Click on the second additional text area"""
    try:
        print("Looking for second text area...")
        text_area = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[2]/section[3]/div[2]/div[2]/div/div[2]/div/div/div/div/div"))
        )
        
        print("Clicking second text area...")
        text_area.click()
        
        print("✅ Second text area clicked successfully!")
        take_screenshot(driver, "second_text_area_clicked.png")
        return True
        
    except Exception as e:
        print(f"❌ Error clicking second text area: {str(e)}")
        take_screenshot(driver, "second_text_area_error.png")
        return False

def fill_reels_input(driver):
    """Fill the reels input field"""
    try:
        print("Looking for reels input field...")
        reels_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[2]/section[3]/div[2]/div[2]/div/div[4]/div/div[1]/div/input"))
        )
        
        print("Filling reels input...")
        reels_input.click()
        reels_input.clear()
        reels_input.send_keys("#reels")
        
        print("✅ Reels input filled successfully!")
        take_screenshot(driver, "reels_input_filled.png")
        return True
        
    except Exception as e:
        print(f"❌ Error filling reels input: {str(e)}")
        take_screenshot(driver, "reels_input_error.png")
        return False

def click_section_button(driver):
    """Click on the button in section 4"""
    try:
        print("Looking for section button...")
        section_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[2]/section[4]/div/div[2]/div/div/div/div/div/div[1]"))
        )
        
        print("Clicking section button...")
        section_button.click()
        
        print("✅ Section button clicked successfully!")
        take_screenshot(driver, "section_button_clicked.png")
        return True
        
    except Exception as e:
        print(f"❌ Error clicking section button: {str(e)}")
        take_screenshot(driver, "section_button_error.png")
        return False

def click_list_item(driver):
    """Click on the list item"""
    try:
        print("Looking for list item...")
        list_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[2]/section[4]/div/div[2]/div/div/div/div/div/div[2]/ul/li[1]/div/p"))
        )
        
        print("Clicking list item...")
        list_item.click()
        
        print("✅ List item clicked successfully!")
        take_screenshot(driver, "list_item_clicked.png")
        return True
        
    except Exception as e:
        print(f"❌ Error clicking list item: {str(e)}")
        take_screenshot(driver, "list_item_error.png")
        return False

def main():
    try:
        print("Starting Chrome...")
        driver = setup_chrome()
        
        # Load existing session cookies
        if not load_cookies(driver):
            print("❌ No session cookies found. Please run login.py first.")
            return None
        
        print("🚀 Session restored successfully!")
        
        # Click the New Post button
        if not click_new_post(driver):
            print("❌ Failed to click New Post button")
            return None
        
        # Upload video
        if not upload_video(driver):
            print("❌ Failed to upload video")
            return None
        
        # Type content
        if not type_content(driver):
            print("❌ Failed to type content")
            return None
        
        # Click customize button
        if not click_customize_button(driver):
            print("❌ Failed to click customize button")
            return None
        
        # Click second text area
        if not click_second_text_area(driver):
            print("❌ Failed to click second text area")
            return None
        
        # Fill reels input
        if not fill_reels_input(driver):
            print("❌ Failed to fill reels input")
            return None
        
        # Click section button
        if not click_section_button(driver):
            print("❌ Failed to click section button")
            return None
        
        # Click list item
        if not click_list_item(driver):
            print("❌ Failed to click list item")
            return None
        
        print("\n🚀 All steps completed successfully!")
        return driver
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if 'driver' in locals():
            take_screenshot(driver, "main_exception.png")
        return None

if __name__ == "__main__":
    driver = main()
    
    if driver:
        print("\n✅ Post creation process completed!")
        input("Press Enter to close the browser...")
        driver.quit()
