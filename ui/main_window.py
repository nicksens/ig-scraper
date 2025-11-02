import customtkinter as ctk
from tkinter import messagebox



class ReelScraperWindow(ctk.CTk):
    """Main GUI window for the Instagram Reels Scraper."""
    
    def __init__(self, account_manager, scraper_controller):
        super().__init__()
        
        self.account_manager = account_manager
        self.scraper_controller = scraper_controller
        
        self.title("Instagram Reels Scraper")
        self.geometry("1000x700")
        self.minsize(900, 650)
        
        self.create_widgets()
        self.after(100, self.process_log_queue)
    
    def create_widgets(self):
        """Creates and configures the GUI elements."""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left Frame (Controls)
        controls_frame = ctk.CTkFrame(self, width=280)
        controls_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ns")
        controls_frame.grid_propagate(False)
        
        ctk.CTkLabel(controls_frame, text="Reels Scraper", 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(10, 20))
        
        self._create_account_section(controls_frame)
        self._create_scraping_section(controls_frame)
        self._create_control_buttons(controls_frame)
        
        # Right Frame (Logs - FULL SIZE)
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(log_frame, text="📋 Activity Log", 
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
                         row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        self.log_textbox = ctk.CTkTextbox(
            log_frame, 
            state="disabled", 
            font=("Consolas", 12),
            wrap="word"
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
    
    def _create_account_section(self, parent):
        account_frame = ctk.CTkFrame(parent)
        account_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(account_frame, text="Account", 
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 10))
        
        usernames = self.account_manager.get_all_usernames() or ["No accounts"]
        self.account_selector = ctk.CTkComboBox(
            account_frame, values=usernames, command=self.on_account_select
        )
        self.account_selector.pack(pady=5, padx=10, fill="x")
        
        self.username_entry = ctk.CTkEntry(account_frame, placeholder_text="Username")
        self.username_entry.pack(pady=5, padx=10, fill="x")
        
        self.password_entry = ctk.CTkEntry(account_frame, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=5, padx=10, fill="x")
        
        btn_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
        btn_frame.pack(pady=8, padx=10, fill="x")
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(btn_frame, text="Save", command=self.save_account, height=32).grid(
            row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(btn_frame, text="Delete", command=self.delete_account, height=32,
                      fg_color="#D32F2F", hover_color="#C62828").grid(
            row=0, column=1, padx=(5, 0), sticky="ew")
    
    def _create_scraping_section(self, parent):
        scraping_frame = ctk.CTkFrame(parent)
        scraping_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(scraping_frame, text="Settings",
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 10))
        
        # Mode selection
        self.mode_var = ctk.StringVar(value="auto")
        mode_frame = ctk.CTkFrame(scraping_frame, fg_color="transparent")
        mode_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkRadioButton(mode_frame, text="Auto", variable=self.mode_var, 
                          value="auto", font=ctk.CTkFont(size=12),
                          command=self.on_mode_change).pack(side="left", padx=8)
        ctk.CTkRadioButton(mode_frame, text="Manual", variable=self.mode_var, 
                          value="manual", font=ctk.CTkFont(size=12),
                          command=self.on_mode_change).pack(side="left", padx=8)
        
        # Number of reels
        self.limit_entry = ctk.CTkEntry(scraping_frame, placeholder_text="Number of Reels", height=35)
        self.limit_entry.pack(pady=8, padx=10, fill="x")
        
        # Minimum likes (only for auto mode)
        self.min_likes_entry = ctk.CTkEntry(scraping_frame, placeholder_text="Min Likes (Auto Mode)", height=35)
        self.min_likes_entry.insert(0, "10000")  # Default value
        self.min_likes_entry.pack(pady=8, padx=10, fill="x")
        
        # Info box
        self.info_frame = ctk.CTkFrame(scraping_frame, fg_color="#1a4d2e", corner_radius=8)
        self.info_frame.pack(pady=8, padx=10, fill="x")
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Auto Mode:\n✅ Saves reels with\nmin likes threshold",
            font=ctk.CTkFont(size=11),
            text_color="#4CAF50",
            justify="center"
        )
        self.info_label.pack(pady=10)
    
    def on_mode_change(self):
        """Update info box when mode changes."""
        if self.mode_var.get() == "manual":
            self.info_label.configure(
                text="Manual Mode:\nENTER = ❤️ Like + Save\nBACKSPACE = Skip"
            )
            self.min_likes_entry.configure(state="disabled")
        else:
            self.info_label.configure(
                text="Auto Mode:\n✅ Saves reels with\nmin likes threshold"
            )
            self.min_likes_entry.configure(state="normal")
    
    def _create_control_buttons(self, parent):
        self.start_button = ctk.CTkButton(
            parent, text="▶ Start Scraping", command=self.start_scraping,
            height=45, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2ECC71", hover_color="#27AE60"
        )
        self.start_button.pack(pady=(25, 8), padx=20, fill="x")
        
        self.stop_button = ctk.CTkButton(
            parent, text="⬛ Stop", command=self.stop_scraping,
            fg_color="#E74C3C", hover_color="#C0392B", state="disabled", height=45,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.stop_button.pack(pady=8, padx=20, fill="x")
    
    def on_account_select(self, selected_username):
        password = self.account_manager.get_account(selected_username)
        if password:
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, selected_username)
            self.password_entry.delete(0, "end")
            self.password_entry.insert(0, password)
    
    def save_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        success, message = self.account_manager.add_or_update_account(username, password)
        if success:
            self.update_account_dropdown()
            self.account_selector.set(username)
            messagebox.showinfo("Success", message)
        else:
            messagebox.showwarning("Error", message)
    
    def delete_account(self):
        selected_username = self.account_selector.get()
        if selected_username == "No accounts":
            messagebox.showwarning("No Account", "Select a valid account.")
            return
        if messagebox.askyesno("Confirm", f"Delete '{selected_username}'?"):
            success, message = self.account_manager.delete_account(selected_username)
            if success:
                self.update_account_dropdown()
                self.username_entry.delete(0, "end")
                self.password_entry.delete(0, "end")
                messagebox.showinfo("Success", message)
    
    def update_account_dropdown(self):
        usernames = self.account_manager.get_all_usernames() or ["No accounts"]
        self.account_selector.configure(values=usernames)
        if not self.account_manager.get_all_usernames():
            self.account_selector.set("No accounts")
    
    def start_scraping(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            reel_limit = int(self.limit_entry.get())
            if reel_limit <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Enter a positive number for reels.")
            return
        
        if not username or not password:
            messagebox.showwarning("Missing Info", "Enter credentials.")
            return
        
        manual_mode = (self.mode_var.get() == "manual")
        
        # Get minimum likes for auto mode
        min_likes = 0
        if not manual_mode:
            try:
                min_likes = int(self.min_likes_entry.get())
                if min_likes < 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid", "Enter a valid number for minimum likes.")
                return
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        self.scraper_controller.start_scraping(username, password, reel_limit, manual_mode, min_likes)
    
    def stop_scraping(self):
        self.scraper_controller.stop_scraping()
        self.stop_button.configure(state="disabled")
    
    def on_scraping_complete(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
    
    def process_log_queue(self):
        messages = self.scraper_controller.get_log_messages()
        if messages:
            self.log_textbox.configure(state="normal")
            for message in messages:
                self.log_textbox.insert("end", message)
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")
        self.after(100, self.process_log_queue)
    
    def show_confirmation_dialog(self, title, message):
        return messagebox.askyesno(title, message)
