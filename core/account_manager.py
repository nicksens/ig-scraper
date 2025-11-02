import json
import os


class AccountManager:
    """Manages user account storage and retrieval."""
    
    def __init__(self, accounts_file="accounts.json"):
        self.accounts_file = accounts_file
        self.accounts = {}
        self.load_accounts()
    
    def load_accounts(self):
        """Loads accounts from the JSON file."""
        try:
            with open(self.accounts_file, "r") as f:
                self.accounts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.accounts = {}
    
    def save_accounts(self):
        """Saves the current accounts to the JSON file."""
        with open(self.accounts_file, "w") as f:
            json.dump(self.accounts, f, indent=4)
    
    def add_or_update_account(self, username, password):
        """Adds or updates an account."""
        if not username or not password:
            return False, "Username and password cannot be empty"
        
        self.accounts[username] = password
        self.save_accounts()
        return True, f"Account '{username}' has been saved"
    
    def delete_account(self, username):
        """Deletes an account by username."""
        if username not in self.accounts:
            return False, "Account not found"
        
        del self.accounts[username]
        self.save_accounts()
        return True, f"Account '{username}' has been deleted"
    
    def get_account(self, username):
        """Retrieves account credentials by username."""
        return self.accounts.get(username)
    
    def get_all_usernames(self):
        """Returns a list of all saved usernames."""
        return list(self.accounts.keys())
