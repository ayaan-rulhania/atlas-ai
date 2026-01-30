"""
Poseidon Voice Assistant Module
Handles voice recognition, text-to-speech, and voice interaction features
Enhanced with voice commands, emotion detection, and advanced context management
Version 3.0.0: Multi-language support, adaptive listening, smart interruptions, and more
"""

__version__ = "3.0.0"

from .voice_handler import (
    PoseidonVoiceHandler,
    VoiceCommandType,
    EmotionType,
    get_voice_handler
)

__all__ = [
    'PoseidonVoiceHandler',
    'VoiceCommandType',
    'EmotionType',
    'get_voice_handler',
    '__version__'
]

