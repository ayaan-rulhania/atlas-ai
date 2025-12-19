"""
Poseidon Voice Handler - Comprehensive Voice Processing Backend
Handles audio processing, transcription, and voice interaction management
"""

import json
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class PoseidonVoiceHandler:
    """Comprehensive voice recognition and synthesis handler for Poseidon"""
    
    def __init__(self):
        self.is_active = False
        self.is_paused = False
        self.current_transcript = ""
        self.transcript_history: List[Dict] = []
        self.audio_level_threshold = 0.01  # Minimum audio level to consider as speech
        self.silence_duration = 2.0  # Seconds of silence before processing
        self.min_transcript_length = 2  # Minimum characters to process
        
    def validate_transcript(self, transcript: str) -> Tuple[bool, Optional[str]]:
        """
        Validate and clean transcript before processing.
        
        Args:
            transcript: Raw transcript from speech recognition
            
        Returns:
            Tuple of (is_valid, cleaned_transcript)
        """
        if not transcript:
            return False, None
            
        # Clean transcript
        cleaned = transcript.strip()
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Check minimum length
        if len(cleaned) < self.min_transcript_length:
            return False, None
            
        # Check for common false positives
        false_positives = [
            'uh', 'um', 'ah', 'eh', 'oh',
            'hmm', 'huh', 'er', 'well',
            'like', 'you know', 'i mean'
        ]
        
        cleaned_lower = cleaned.lower()
        if cleaned_lower in false_positives:
            return False, None
            
        # Check if it's just punctuation or noise
        if re.match(r'^[^\w\s]+$', cleaned):
            return False, None
            
        return True, cleaned
    
    def process_transcript(self, transcript: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Process a transcript and prepare it for chat API.
        
        Args:
            transcript: The transcript text
            metadata: Optional metadata (confidence, language, etc.)
            
        Returns:
            Dictionary with processed transcript and metadata
        """
        is_valid, cleaned = self.validate_transcript(transcript)
        
        if not is_valid:
            return {
                'valid': False,
                'reason': 'Transcript too short or invalid',
                'original': transcript
            }
        
        # Add to history
        transcript_entry = {
            'text': cleaned,
            'original': transcript,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.transcript_history.append(transcript_entry)
        
        # Keep only last 50 entries
        if len(self.transcript_history) > 50:
            self.transcript_history = self.transcript_history[-50:]
        
        return {
            'valid': True,
            'transcript': cleaned,
            'original': transcript,
            'confidence': metadata.get('confidence', 0.0) if metadata else 0.0,
            'timestamp': transcript_entry['timestamp']
        }
    
    def get_transcript_context(self, limit: int = 5) -> List[str]:
        """
        Get recent transcript history for context.
        
        Args:
            limit: Number of recent transcripts to return
            
        Returns:
            List of recent transcript texts
        """
        recent = self.transcript_history[-limit:] if len(self.transcript_history) > limit else self.transcript_history
        return [entry['text'] for entry in recent if entry.get('text')]
    
    def reset(self):
        """Reset handler state."""
        self.is_active = False
        self.is_paused = False
        self.current_transcript = ""
        self.transcript_history = []
    
    def set_active(self, active: bool):
        """Set active state."""
        self.is_active = active
        if not active:
            self.current_transcript = ""
    
    def set_paused(self, paused: bool):
        """Set paused state."""
        self.is_paused = paused


# Global instance
_voice_handler: Optional[PoseidonVoiceHandler] = None


def get_voice_handler() -> PoseidonVoiceHandler:
    """Get or create global voice handler instance."""
    global _voice_handler
    if _voice_handler is None:
        _voice_handler = PoseidonVoiceHandler()
    return _voice_handler
