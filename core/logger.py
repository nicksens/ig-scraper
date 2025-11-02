import time
from queue import Queue


class ScraperLogger:
    """Thread-safe logging system for the scraper."""
    
    def __init__(self):
        self.log_queue = Queue()
    
    def log(self, message):
        """Adds a timestamped message to the log queue."""
        timestamp = time.strftime('%H:%M:%S')
        self.log_queue.put(f"[{timestamp}] {message}\n")
    
    def get_messages(self):
        """Retrieves all pending log messages."""
        messages = []
        while not self.log_queue.empty():
            messages.append(self.log_queue.get_nowait())
        return messages
    
    def has_messages(self):
        """Checks if there are pending messages."""
        return not self.log_queue.empty()
