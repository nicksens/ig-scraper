import time
import random
import threading
from pynput import keyboard
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import pytesseract
from PIL import Image
import re
import pyperclip


# Set tesseract path (adjust if your installation path is different)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ReelsScraper:
    """Handles the Instagram Reels scraping logic."""
    
    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler
        self.driver = None
        self.stop_event = None
        self.user_action_event = None
        self.user_action = None
        self.keyboard_listener = None
        self.wait = None
    
    def setup_driver(self):
        """Initializes the Chrome WebDriver."""
        # Configure PyAutoGUI
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
        
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Make Chrome window compact and at fixed position
        chrome_options.add_argument("--window-size=600,800")
        chrome_options.add_argument("--window-position=850,100")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.logger.log("🌐 Chrome browser opened")
    
    def start_global_keyboard_listener(self):
        """Starts a global keyboard listener for ENTER and BACKSPACE."""
        def on_press(key):
            try:
                if not self.user_action_event:
                    return
                
                if key == keyboard.Key.enter:
                    self.user_action = 'save'
                    self.user_action_event.set()
                    self.logger.log("✅ ENTER - Liking & saving...")
                
                elif key == keyboard.Key.backspace:
                    self.user_action = 'skip'
                    self.user_action_event.set()
                    self.logger.log("⏭️ BACKSPACE - Skipping...")
                    
            except AttributeError:
                pass
        
        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        self.keyboard_listener.start()
        self.logger.log("🎹 Keyboard shortcuts active!")
    
    def stop_global_keyboard_listener(self):
        """Stops the global keyboard listener."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
    
    def login(self, username, password):
        """Performs the Instagram login process."""
        self.driver.get("https://www.instagram.com/accounts/login/")
        self.logger.log("😴 Loading login page...")
        time.sleep(random.uniform(2, 4))
        
        self.logger.log(f"👤 Logging in as {username}...")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        self.logger.log("⏳ Submitting credentials...")
        time.sleep(random.uniform(5, 8))
    
    def navigate_to_reels(self):
        """Navigate to Instagram Reels feed."""
        self.logger.log("🎬 Opening Reels feed...")
        self.driver.get("https://www.instagram.com/reels/")
        time.sleep(random.uniform(4, 6))
    
    def calibrate_like_button_position(self):
        """
        Dummy calibration method for compatibility.
        Since we're using pure Selenium, no actual calibration is needed.
        """
        try:
            self.logger.log("🎯 Checking for like button...")
            time.sleep(1)
            
            # Just verify we can find like buttons
            like_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                'svg[aria-label="Like"], svg[aria-label="Unlike"]')
            
            if like_buttons:
                self.logger.log(f"✅ Found {len(like_buttons)} like button(s)")
                return True
            else:
                self.logger.log("⚠️ No like buttons found yet")
                return False
                
        except Exception as e:
            self.logger.log(f"⚠️ Check failed: {str(e)[:80]}")
            return False
    
    def get_current_reel_likes(self):
        """
        Gets like count from the currently VISIBLE/ACTIVE reel only
        
        Returns:
            str: The like count text
        """
        try:
            # Use JavaScript to find ONLY elements in the viewport
            like_text = self.driver.execute_script("""
                // Function to check if element is in viewport
                function isInViewport(element) {
                    const rect = element.getBoundingClientRect();
                    return (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                    );
                }
                
                // Find all span elements
                var spans = document.querySelectorAll('span');
                
                for (var i = 0; i < spans.length; i++) {
                    // Only check if element is in viewport
                    if (!isInViewport(spans[i])) continue;
                    
                    var text = spans[i].innerText.trim();
                    
                    // Check if it's a like count (contains numbers and optionally K/M/B)
                    if (text.match(/^\\d+[.,]?\\d*[KMB]?\\s*(likes?)?$/i)) {
                        // Make sure it's short (actual like count, not a paragraph)
                        if (text.length < 20) {
                            return text;
                        }
                    }
                }
                
                return 'Unknown';
            """)
            
            # Clean up the result
            if like_text and like_text != 'Unknown':
                # Remove " likes" if present
                cleaned = re.sub(r'\s*likes?\s*$', '', like_text, flags=re.IGNORECASE).strip()
                self.logger.log(f"👍 Detected likes: {cleaned}")
                return cleaned
            
            return "Unknown"
            
        except Exception as e:
            self.logger.log(f"⚠️ Failed to get likes: {str(e)[:60]}")
            return "Unknown"
    
    def parse_like_count_to_number(self, like_text):
        """
        Converts like count text to actual number
        
        Args:
            like_text: String like "10.5K", "1.2M", "500", etc.
        
        Returns:
            int: Actual number of likes
        """
        try:
            if not like_text or like_text == "Unknown":
                return 0
            
            # Remove any extra text
            like_text = like_text.strip().upper()
            like_text = re.sub(r'\s*LIKES?\s*$', '', like_text, flags=re.IGNORECASE)
            
            # Extract number and unit
            match = re.search(r'([\d.,]+)\s*([KMB])?', like_text)
            if not match:
                return 0
            
            number_str = match.group(1).replace(',', '.')
            unit = match.group(2) if match.group(2) else None
            
            number = float(number_str)
            
            # Convert to actual number
            if unit == 'K':
                return int(number * 1000)
            elif unit == 'M':
                return int(number * 1000000)
            elif unit == 'B':
                return int(number * 1000000000)
            else:
                return int(number)
                
        except Exception as e:
            self.logger.log(f"⚠️ Parse error: {str(e)[:50]}")
            return 0
    
    def like_current_reel(self):
        """
        Likes the current reel using pure Selenium with retry logic.
        FIXED: Uses is_displayed() to find the ACTIVE button, avoiding stale elements.
        """
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                time.sleep(0.8)
                like_count = self.get_current_reel_likes()
                
                # --- START FIX: Find the VISIBLE Like button ---
                like_button = None
                try:
                    # Find ALL potential like buttons
                    all_like_buttons = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'svg[aria-label="Like"]'))
                    )
                    
                    # Find the one that is actually visible
                    for btn in all_like_buttons:
                        if btn.is_displayed():
                            like_button = btn
                            break
                    
                    if not like_button:
                        # If no button was found in the loop, raise an error to be caught below
                        raise Exception("No *visible* 'Like' button found")
                        
                except:
                    pass # The 'pass' here is from the original code, it will flow to the 'if not like_button:' check
                # --- END FIX ---
                
                # If no visible Like button, check if already liked (using the same visibility logic)
                if not like_button:
                    try:
                        # --- START FIX: Find the VISIBLE Unlike button ---
                        all_unlike_buttons = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'svg[aria-label="Unlike"]'))
                        )
                        visible_unlike_button = None
                        for btn in all_unlike_buttons:
                            if btn.is_displayed():
                                visible_unlike_button = btn
                                break
                        # --- END FIX ---
                        
                        if visible_unlike_button:
                            self.logger.log(f"ℹ️ Already liked (had {like_count} likes)")
                            return True
                        else:
                            # No visible Like OR Unlike button
                            raise Exception("No visible Like or Unlike button found")
                            
                    except:
                        self.logger.log(f"⚠️ No visible like/unlike button found (attempt {attempt + 1})")
                        if attempt < max_attempts - 1:
                            time.sleep(1)
                            continue
                        else:
                            self.logger.log("❌ Trying double-tap fallback...")
                            result = self.double_tap_video()
                            return result
                
                # Find clickable element (your logic here is fine)
                try:
                    clickable = like_button.find_element(By.XPATH, 
                        './ancestor::button | ./ancestor::span[@role="button"] | ./parent::span/parent::div')
                except:
                    try:
                        clickable = like_button.find_element(By.XPATH, './parent::*')
                    except:
                        clickable = like_button
                
                # CLICK IT
                self.driver.execute_script("arguments[0].click();", clickable)
                self.logger.log(f"🖱️ Clicked like button (attempt {attempt + 1})")
                
                # VERIFY the like worked by checking for the VISIBLE Unlike button
                time.sleep(1.0)
                
                unlike_found = False
                try:
                    # --- START FIX: Find the VISIBLE Unlike button for verification ---
                    all_unlike_buttons = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'svg[aria-label="Unlike"]'))
                    )
                    for btn in all_unlike_buttons:
                        if btn.is_displayed():
                            unlike_found = True
                            break
                    # --- END FIX ---
                            
                    if unlike_found:
                        self.logger.log(f"✅ VERIFIED! Button changed to Unlike")
                    else:
                        raise Exception("Verification failed - no visible Unlike button")
                except:
                    self.logger.log(f"⚠️ Verification failed - button didn't change (attempt {attempt + 1})")
                
                if unlike_found:
                    self.logger.log(f"❤️ Liked! (had {like_count} likes)")
                    time.sleep(0.5)
                    return True
                else:
                    # Click didn't work, retry
                    if attempt < max_attempts - 1:
                        self.logger.log(f"⚠️ Retrying... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(1)
                        continue
                    else:
                        self.logger.log("❌ Like failed, trying double-tap...")
                        result = self.double_tap_video()
                        return result
                        
            except Exception as e:
                self.logger.log(f"⚠️ Exception (attempt {attempt + 1}): {str(e)[:60]}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                else:
                    self.logger.log("❌ Exception on final attempt, trying double-tap...")
                    result = self.double_tap_video()
                    return result
        
        self.logger.log("❌ Could not like reel")
        return False

    
    def double_tap_video(self):
        """Fallback: Double-tap the video to like."""
        try:
            video = self.driver.find_element(By.TAG_NAME, "video")
            action = ActionChains(self.driver)
            action.double_click(video).perform()
            self.logger.log("❤️ Liked (double-tap)")
            time.sleep(0.3)
            return True
        except:
            return False
    
    def scroll_to_next_reel(self):
        """Scrolls down to the next reel using JavaScript (bypass click interception)."""
        try:
            # Method 1: Use JavaScript to dispatch keyboard event directly
            # This bypasses any overlay/popup blocking issues
            self.driver.execute_script("""
                // Dispatch arrow down keyboard event
                var event = new KeyboardEvent('keydown', {
                    key: 'ArrowDown',
                    code: 'ArrowDown',
                    keyCode: 40,
                    which: 40,
                    bubbles: true
                });
                document.dispatchEvent(event);
            """)
            
            self.logger.log("⬇️ Next reel")
            
            # Wait for new reel to load and URL to change
            old_url = self.driver.current_url
            time.sleep(random.uniform(2.5, 3.0))
            
            # Verify URL changed (means scroll worked)
            new_url = self.driver.current_url
            if old_url == new_url:
                self.logger.log("⚠️ URL didn't change, trying alternative scroll...")
                # Fallback: Send key to body element
                ActionChains(self.driver).send_keys(Keys.ARROW_DOWN).perform()
                time.sleep(2.0)
            
            return True
            
        except Exception as e:
            self.logger.log(f"⚠️ Scroll error: {str(e)[:60]}")
            # Last resort: try arrow down on body
            try:
                ActionChains(self.driver).send_keys(Keys.ARROW_DOWN).perform()
                time.sleep(2.0)
                return True
            except:
                return False


    
    def get_current_url(self):
        """Get current URL from browser."""
        return self.driver.current_url
    
    def scroll_down(self):
        """Scroll the page down."""
        ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()
    
    def cleanup(self):
        """Cleanup resources."""
        self.stop_global_keyboard_listener()
        if self.driver:
            self.driver.quit()
    
    def set_stop_event(self, event):
        self.stop_event = event
    
    def set_user_action_event(self, event):
        self.user_action_event = event
