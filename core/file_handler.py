import os
import datetime


class FileHandler:
    """Handles file operations for saving scraped links."""
    
    @staticmethod
    def get_output_filename():
        """Generates a unique filename in the format MM-DD-N.txt."""
        today = datetime.datetime.now().strftime("%m-%d")
        i = 1
        while True:
            filename = f"{today}-{i}.txt"
            if not os.path.exists(filename):
                return filename
            i += 1
    
    @staticmethod
    def save_links_to_file(links_set, filename):
        """Saves the current set of links to the specified file."""
        with open(filename, "w") as f:
            for link in sorted(list(links_set)):
                f.write(f"{link}\n")
        return len(links_set)
