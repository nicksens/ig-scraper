from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import QUrl


class BrowserManager:
    """Manages the embedded browser using QtWebEngine."""
    
    def __init__(self, logger):
        self.logger = logger
        self.browser_widget = None
        self.web_view = None
    
    def initialize(self):
        """Initialize the browser."""
        self.logger.log("🌐 Browser engine initialized")
    
    def create_browser_widget(self):
        """Creates the browser widget."""
        self.browser_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        
        # Enable JavaScript and other features
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        
        layout.addWidget(self.web_view)
        self.browser_widget.setLayout(layout)
        
        self.logger.log("✅ Browser widget created")
        return self.browser_widget
    
    def navigate_to(self, url):
        """Navigate to a URL."""
        if self.web_view:
            self.web_view.setUrl(QUrl(url))
            self.logger.log(f"📱 Navigating to: {url}")
    
    def get_current_url(self):
        """Get the current URL."""
        if self.web_view:
            return self.web_view.url().toString()
        return None
    
    def execute_javascript(self, js_code, callback=None):
        """Execute JavaScript in the browser."""
        if self.web_view:
            if callback:
                self.web_view.page().runJavaScript(js_code, callback)
            else:
                self.web_view.page().runJavaScript(js_code)
    
    def scroll_down(self):
        """Scroll the page down."""
        js_code = "window.scrollBy(0, window.innerHeight);"
        self.execute_javascript(js_code)
    
    def shutdown(self):
        """Cleanup."""
        pass
