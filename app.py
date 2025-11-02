import threading
from tkinter import messagebox
import time
import random


from core.account_manager import AccountManager
from core.scraper import ReelsScraper
from core.file_handler import FileHandler
from core.logger import ScraperLogger
from ui.main_window import ReelScraperWindow



class ScraperController:
    """Controller that coordinates between UI and core functionality."""
    
    def __init__(self):
        self.logger = ScraperLogger()
        self.file_handler = FileHandler()
        self.scraper = ReelsScraper(self.logger, self.file_handler)
        
        self.scraper_thread = None
        self.stop_event = None
        self.user_action_event = None
        self.manual_mode = False
        self.window = None
    
    def set_window(self, window):
        self.window = window
    
    def is_scraping(self):
        return self.scraper_thread and self.scraper_thread.is_alive()
    
    def start_scraping(self, username, password, reel_limit, manual_mode, min_likes=0):
        """
        Start scraping process
        
        Args:
            username: Instagram username
            password: Instagram password
            reel_limit: Target number of reels to collect
            manual_mode: If True, user controls with keyboard. If False, auto-scrapes by likes
            min_likes: Minimum likes threshold for automatic mode (ignored in manual mode)
        """
        self.manual_mode = manual_mode
        
        if manual_mode:
            self.logger.log("=" * 50)
            self.logger.log("🎮 MANUAL MODE ACTIVATED")
            self.logger.log("=" * 50)
            self.logger.log("Press ENTER to LIKE + SAVE reel")
            self.logger.log("Press BACKSPACE to SKIP reel")
            self.logger.log("=" * 50)
        else:
            self.logger.log("=" * 50)
            self.logger.log("🤖 AUTOMATIC MODE ACTIVATED")
            self.logger.log("=" * 50)
            self.logger.log(f"Minimum likes required: {min_likes:,}")
            self.logger.log(f"Target reels: {reel_limit}")
            self.logger.log("=" * 50)
        
        self.stop_event = threading.Event()
        self.user_action_event = threading.Event()
        
        self.scraper.set_stop_event(self.stop_event)
        self.scraper.set_user_action_event(self.user_action_event)
        
        self.scraper_thread = threading.Thread(
            target=self._run_scraping_process,
            args=(username, password, reel_limit, manual_mode, min_likes),
            daemon=True
        )
        self.scraper_thread.start()
    
    def _run_scraping_process(self, username, password, reel_limit, manual_mode, min_likes):
        try:
            self.logger.log("🚀 Starting scraper...")
            
            # Setup browser
            self.scraper.setup_driver()
            
            # Login
            self.scraper.login(username, password)
            
            # Wait for confirmation
            self.logger.log("⏸️ Please complete login (handle 2FA if needed)")
            
            confirmation_needed = threading.Event()
            user_confirmed = [False]
            
            def ask_confirmation():
                result = self.window.show_confirmation_dialog(
                    "Login Confirmation",
                    "Have you successfully logged in?\n\n"
                    "Click YES to start scraping.\n"
                    "Click NO to cancel."
                )
                user_confirmed[0] = result
                confirmation_needed.set()
            
            self.window.after(0, ask_confirmation)
            confirmation_needed.wait()
            
            if not user_confirmed[0]:
                self.logger.log("❌ Canceled by user")
                return
            
            self.logger.log("✅ Starting scrape process...")
            
            # Navigate to reels
            self.scraper.navigate_to_reels()

            # Calibrate like button position
            self.logger.log("🎯 Calibrating like button...")
            if not self.scraper.calibrate_like_button_position():
                self.logger.log("⚠️ Calibration failed, will use fallback methods")
            else:
                self.logger.log("✅ Ready to scrape!")

            # Setup output file
            filename = self.file_handler.get_output_filename()
            self.logger.log(f"📝 Saving to: {filename}")
            self.logger.log(f"🎯 Target: {reel_limit} reels")
            self.logger.log("-" * 50)
            
            # Start scraping based on mode
            if manual_mode:
                self._run_manual_mode(reel_limit, filename)
            else:
                self._run_automatic_mode(reel_limit, min_likes, filename)
            
        except Exception as e:
            self.logger.log(f"❌ ERROR: {e}")
            import traceback
            self.logger.log(traceback.format_exc())
            error_msg = str(e)
            self.window.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.scraper.cleanup()
            self.logger.log("🎉 Browser closed")
            self.window.after(0, self.window.on_scraping_complete)
    
    def _run_manual_mode(self, reel_limit, filename):
        """Run manual mode with keyboard controls."""
        reel_links = set()
        self.scraper.start_global_keyboard_listener()
        
        try:
            while len(reel_links) < reel_limit:
                if self.stop_event.is_set():
                    self.logger.log("🛑 Stopped by user")
                    break
                
                # Get URL
                current_url = self.scraper.get_current_url()
                
                if current_url and "/reels/" in current_url and len(current_url.split('/')) >= 5:
                    if current_url not in reel_links:
                        reel_id = current_url.split('/')[-2][-12:]
                        
                        # Get like count
                        like_count = self.scraper.get_current_reel_likes()
                        self.logger.log(f"\n🎥 NEW REEL: ...{reel_id}")
                        self.logger.log(f"❤️ Likes: {like_count}")
                        
                        self.logger.log("⏸️ WAITING - Press ENTER to Like+Save or BACKSPACE to Skip")
                        self.user_action_event.clear()
                        self.scraper.user_action = None
                        
                        self.user_action_event.wait()
                        
                        if self.stop_event.is_set():
                            break
                        
                        if self.scraper.user_action == 'save':
                            # Like the reel
                            self.scraper.like_current_reel()
                            time.sleep(0.5)
                            
                            # Save URL
                            reel_links.add(current_url)
                            self.logger.log(f"💾 SAVED #{len(reel_links)}")
                            
                            # Scroll to next reel
                            self.scraper.scroll_to_next_reel()
                            
                        elif self.scraper.user_action == 'skip':
                            self.logger.log("⏭️ SKIPPED - Moving to next reel")
                            # Just scroll without liking
                            self.scraper.scroll_to_next_reel()
                        
                        # Backup every 10
                        if len(reel_links) % 10 == 0 and len(reel_links) > 0:
                            self.file_handler.save_links_to_file(reel_links, filename)
                            self.logger.log(f"💾 Backup: {len(reel_links)} links")
                    else:
                        # Already seen this reel, scroll to next
                        time.sleep(1)
                        self.scraper.scroll_to_next_reel()
                else:
                    # Not on a reel page, scroll down
                    self.scraper.scroll_down()
                    time.sleep(2)
            
            # Final save
            self.logger.log("\n" + "=" * 50)
            self.logger.log(f"✅ COMPLETE! Collected {len(reel_links)} reels")
            count = self.file_handler.save_links_to_file(reel_links, filename)
            self.logger.log(f"💾 Saved to: {filename}")
            self.logger.log("=" * 50)
            
        finally:
            self.scraper.stop_global_keyboard_listener()
    
    def _run_automatic_mode(self, reel_limit, min_likes, filename):
        """Run automatic mode based on minimum likes threshold."""
        reel_links = set()
        checked_count = 0
        seen_urls = set()
        consecutive_skips = 0
        max_consecutive_skips = 3
        
        while len(reel_links) < reel_limit:
            if self.stop_event.is_set():
                self.logger.log("🛑 Stopped by user")
                break
            
            try:
                time.sleep(random.uniform(2.0, 3.0))
                
                # Get current URL with retry
                current_url = None
                for _ in range(3):
                    current_url = self.scraper.get_current_url()
                    if current_url and "/reels/" in current_url:
                        break
                    time.sleep(0.5)
                
                # Validate URL
                if not current_url or "/reels/" not in current_url or len(current_url.split('/')) < 5:
                    self.logger.log("⚠️ Not on a valid reel page, scrolling...")
                    self.scraper.scroll_down()
                    time.sleep(2)
                    continue
                
                # Check if duplicate
                if current_url in seen_urls:
                    consecutive_skips += 1
                    self.logger.log(f"⏭️ Already seen, scrolling... ({consecutive_skips}/{max_consecutive_skips})")
                    
                    if consecutive_skips >= max_consecutive_skips:
                        self.logger.log("⚠️ Too many duplicates, stopping")
                        break
                    
                    time.sleep(1)
                    self.scraper.scroll_to_next_reel()
                    continue
                
                # New reel found
                seen_urls.add(current_url)
                consecutive_skips = 0
                checked_count += 1
                reel_id = current_url.split('/')[-2][-12:]
                
                # Get like count
                like_text = self.scraper.get_current_reel_likes()
                like_count = self.scraper.parse_like_count_to_number(like_text)
                
                self.logger.log(f"\n🎥 Reel #{checked_count}: ...{reel_id}")
                self.logger.log(f"❤️ Likes: {like_text} ({like_count:,})")
                
                # Check threshold
                should_scroll = False  # Flag to track if we need to scroll
                
                if like_count >= min_likes:
                    self.logger.log(f"✅ QUALIFIED! ({like_count:,} >= {min_likes:,})")
                    
                    # Stay on video
                    wait_time = random.uniform(3.0, 4.0)
                    self.logger.log(f"⏳ Watching for {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                    # **LIKE IT**
                    like_success = self.scraper.like_current_reel()
                    time.sleep(0.5)
                    
                    if like_success:
                        self.logger.log("✅ Like successful!")
                        reel_links.add(current_url)
                        self.logger.log(f"💾 SAVED #{len(reel_links)}/{reel_limit}")
                    else:
                        self.logger.log(f"❌ Like FAILED, moving to next reel")
                    
                    should_scroll = True  # Always scroll after qualified reel
                    
                else:
                    self.logger.log(f"⏭️ Skipping ({like_count:,} < {min_likes:,})")
                    should_scroll = True  # **CRITICAL: Always scroll after skipping too!**
                
                # Backup every 10
                if len(reel_links) % 10 == 0 and len(reel_links) > 0:
                    self.file_handler.save_links_to_file(reel_links, filename)
                    self.logger.log(f"💾 Backup: {len(reel_links)} links")
                
                # Scroll UNCONDITIONALLY when appropriate
                if should_scroll and len(reel_links) < reel_limit:
                    self.logger.log("📜 Scrolling to next reel...")
                    self.scraper.scroll_to_next_reel()
                    time.sleep(0.5)  # Small buffer after scroll
                            
            except Exception as e:
                self.logger.log(f"⚠️ Error: {str(e)[:80]}")
                try:
                    time.sleep(1)
                    self.scraper.scroll_to_next_reel()
                except:
                    break
        
        # Final save
        self.logger.log("\n" + "=" * 50)
        self.logger.log(f"✅ COMPLETE! Collected {len(reel_links)}/{reel_limit} reels")
        self.logger.log(f"📊 Checked {checked_count} unique reels")
        count = self.file_handler.save_links_to_file(reel_links, filename)
        self.logger.log(f"💾 Saved to: {filename}")
        self.logger.log("=" * 50)



        
    def stop_scraping(self):
        if self.stop_event:
            self.logger.log("🛑 Stopping...")
            self.stop_event.set()
            if self.user_action_event:
                self.user_action_event.set()
    
    def get_log_messages(self):
        return self.logger.get_messages()



def main():
    """Main application entry point."""
    account_manager = AccountManager()
    scraper_controller = ScraperController()
    
    window = ReelScraperWindow(account_manager, scraper_controller)
    scraper_controller.set_window(window)
    
    window.mainloop()



if __name__ == "__main__":
    main()
