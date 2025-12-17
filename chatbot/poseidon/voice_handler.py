"""
Poseidon Voice Handler
Manages speech recognition and text-to-speech functionality
"""

class PoseidonVoiceHandler:
    """Handles voice recognition and synthesis for Poseidon"""
    
    def __init__(self):
        self.is_active = False
        self.is_paused = False
        
    def check_browser_support(self):
        """Check if browser supports speech recognition"""
        return ('webkitSpeechRecognition' in window) or ('SpeechRecognition' in window)
    
    def check_secure_context(self):
        """Check if running in secure context (HTTPS or localhost)"""
        return (window.isSecureContext or 
                location.protocol === 'https:' or 
                location.hostname === 'localhost' or 
                location.hostname === '127.0.0.1')

