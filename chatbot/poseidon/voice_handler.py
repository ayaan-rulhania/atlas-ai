"""
Poseidon Voice Handler - Comprehensive Voice Processing Backend
Handles audio processing, transcription, and voice interaction management
Enhanced with voice commands, emotion detection, and advanced context management
"""

import json
import logging
from typing import Dict, Optional, List, Tuple, Set
from datetime import datetime, timedelta
import re
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceCommandType(Enum):
    """Types of voice commands"""
    WAKE = "wake"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    REPEAT = "repeat"
    CLEAR = "clear"
    HELP = "help"
    SETTINGS = "settings"  # New: Change settings
    SPEED = "speed"  # New: Change speech speed
    VOLUME = "volume"  # New: Change volume
    LANGUAGE = "language"  # New: Change language
    NONE = "none"


class EmotionType(Enum):
    """Detected emotion types"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    FRUSTRATED = "frustrated"
    QUESTIONING = "questioning"


class PoseidonVoiceHandler:
    """Comprehensive voice recognition and synthesis handler for Poseidon"""
    
    def __init__(self):
        self.is_active = False
        self.is_paused = False
        self.current_transcript = ""
        self.transcript_history: List[Dict] = []
        self.conversation_context: List[Dict] = []  # Full conversation context
        self.audio_level_threshold = 0.01  # Minimum audio level to consider as speech
        self.silence_duration = 2.0  # Seconds of silence before processing
        self.min_transcript_length = 2  # Minimum characters to process
        
        # Voice command patterns
        self.wake_words: Set[str] = {
            'hey poseidon', 'poseidon', 'wake up', 'activate', 'start listening'
        }
        self.command_patterns = {
            VoiceCommandType.PAUSE: [
                r'\b(pause|stop listening|hold on|wait)\b',
                r'\b(quiet|silence|shush)\b'
            ],
            VoiceCommandType.RESUME: [
                r'\b(resume|continue|keep going|go on)\b',
                r'\b(listen|start listening again)\b'
            ],
            VoiceCommandType.STOP: [
                r'\b(stop|end|exit|close|shut down)\b',
                r'\b(that\'s enough|all done|finished)\b'
            ],
            VoiceCommandType.REPEAT: [
                r'\b(repeat|say that again|what did you say|pardon)\b',
                r'\b(can you repeat|one more time)\b'
            ],
            VoiceCommandType.CLEAR: [
                r'\b(clear|reset|start over|forget)\b',
                r'\b(clear history|reset conversation)\b'
            ],
            VoiceCommandType.HELP: [
                r'\b(help|what can you do|commands|assistance)\b',
                r'\b(how do i|what are|show me)\b'
            ],
            VoiceCommandType.SETTINGS: [
                r'\b(settings|configure|preferences|options)\b'
            ],
            VoiceCommandType.SPEED: [
                r'\b(speed|faster|slower|talk (faster|slower))\b',
                r'\b(speech rate|speaking speed)\b'
            ],
            VoiceCommandType.VOLUME: [
                r'\b(volume|louder|quieter|softer|speak (louder|quieter))\b',
                r'\b(volume (up|down)|turn (up|down))\b'
            ],
            VoiceCommandType.LANGUAGE: [
                r'\b(language|change language|switch language|speak (english|spanish|french|german|hindi|tamil|telugu|mandarin|chinese))\b',
                r'\b(use (english|spanish|french|german|hindi|tamil|telugu|mandarin|chinese|japanese|korean))\b'
            ]
        }
        
        # Emotion detection patterns
        self.emotion_patterns = {
            EmotionType.HAPPY: [
                r'\b(great|awesome|wonderful|excellent|fantastic|amazing|love|happy|joy)\b',
                r'\b(thank you|thanks|appreciate|grateful)\b',
                r'!+',  # Multiple exclamation marks
            ],
            EmotionType.EXCITED: [
                r'\b(wow|yes|yeah|yay|woohoo|awesome|incredible)\b',
                r'\b(cool|neat|sweet|rad|epic)\b',
            ],
            EmotionType.SAD: [
                r'\b(sad|depressed|down|unhappy|disappointed|sorry)\b',
                r'\b(can\'t|unable|failed|wrong|bad)\b',
            ],
            EmotionType.ANGRY: [
                r'\b(angry|mad|furious|annoyed|frustrated|upset)\b',
                r'\b(stupid|idiot|hate|damn|hell)\b',
            ],
            EmotionType.FRUSTRATED: [
                r'\b(why|how come|doesn\'t work|not working|broken)\b',
                r'\b(confused|don\'t understand|unclear)\b',
            ],
            EmotionType.QUESTIONING: [
                r'\?+',  # Question marks
                r'\b(what|why|how|when|where|who|which)\b',
                r'\b(can you|will you|could you|would you)\b',
            ],
            EmotionType.CALM: [
                r'\b(okay|ok|sure|fine|alright|calm|relax)\b',
                r'\b(please|kindly|gently)\b',
            ]
        }
        
        # Audio quality metrics
        self.audio_quality_history: List[Dict] = []
        self.avg_confidence = 0.0
        self.quality_threshold = 0.7  # Minimum confidence for good quality
        
        # Conversation memory
        self.conversation_turns = 0
        self.last_response_time: Optional[datetime] = None
        self.session_start_time = datetime.now()
        
        # Voice activity detection
        self.speech_segments: List[Dict] = []
        self.current_speech_start: Optional[datetime] = None
        
        # Version 3.0.0: Advanced features
        self.language = 'en-US'  # Current language
        self.detected_languages: List[str] = []  # Language detection history
        self.adaptive_sensitivity = 0.01  # Adaptive audio threshold
        self.speech_speed = 1.0  # Speech synthesis speed (0.5 - 2.0)
        self.speech_volume = 1.0  # Speech synthesis volume (0.0 - 1.0)
        self.supported_languages = {
            'en-US': 'English (US)',
            'en-GB': 'English (UK)',
            'en-AU': 'English (Australia)',
            'en-IN': 'English (India)',
            'hi-IN': 'Hindi (India)',  # Version 3.x: Added
            'ta-IN': 'Tamil (India)',  # Version 3.x: Added
            'te-IN': 'Telugu (India)',  # Version 3.x: Added
            'es-ES': 'Spanish (Spain)',
            'es-MX': 'Spanish (Mexico)',
            'fr-FR': 'French',
            'zh-CN': 'Mandarin (Simplified)',  # Version 3.x: Clarified
            'de-DE': 'German',
            'it-IT': 'Italian',
            'pt-BR': 'Portuguese (Brazil)',
            'ja-JP': 'Japanese',
            'ko-KR': 'Korean'
        }
        
        # Version 3.x: Common speech recognition mis-sayings
        self.mis_saying_corrections = {
            # Common homophones and misrecognitions
            'the': ['teh', 'da', 'de'],
            'to': ['two', 'too', 'tu'],
            'for': ['four', 'fore', 'fro'],
            'you': ['u', 'yu', 'ew'],
            'are': ['r', 'arr'],
            'your': ['ur', 'yore'],
            'their': ['there', 'they\'re'],
            'there': ['their', 'they\'re'],
            'they\'re': ['their', 'there'],
            'it\'s': ['its', 'itz'],
            'its': ['it\'s'],
            'can\'t': ['cant', 'can t', 'cannot'],
            'won\'t': ['wont', 'won t'],
            'don\'t': ['dont', 'don t'],
            'isn\'t': ['isnt', 'is n t'],
            # Numbers
            'one': ['won', 'wan'],
            'two': ['to', 'too'],
            'four': ['for', 'fore'],
            # Common phrases
            'what': ['wut', 'wat'],
            'where': ['ware', 'wear'],
            'when': ['wen'],
            'why': ['y', 'wy'],
            'how': ['ow', 'haw'],
            # Common words
            'hello': ['hallo', 'helo'],
            'thanks': ['thx', 'thank'],
            'please': ['pls', 'pleas'],
            'sorry': ['sory', 'sore'],
            'okay': ['ok', 'o k'],
            'yes': ['yess', 'yas'],
            'no': ['know', 'noe']
        }
        self.conversation_summaries: List[Dict] = []  # Conversation summaries
        self.interruptions = 0  # Count of user interruptions
        self.emotion_history: List[Dict] = []  # Emotion tracking over time
        
    def detect_voice_command(self, transcript: str) -> Tuple[VoiceCommandType, Optional[str], Optional[Dict]]:
        """
        Detect if transcript contains a voice command.
        Version 3.0.0: Enhanced with parameter extraction.
        
        Args:
            transcript: The transcript text
            
        Returns:
            Tuple of (command_type, remaining_text, parameters)
        """
        cleaned = transcript.strip().lower()
        params = {}
        
        # Check for wake words
        for wake_word in self.wake_words:
            if wake_word in cleaned:
                # Remove wake word and return remaining text
                remaining = re.sub(rf'\b{re.escape(wake_word)}\b', '', cleaned, flags=re.IGNORECASE).strip()
                return VoiceCommandType.WAKE, remaining if remaining else None, None
        
        # Check for command patterns with parameter extraction
        # Speed command with value
        speed_match = re.search(r'\b(speed|faster|slower|talk (faster|slower))\s*(up|down|to)?\s*(\d+\.?\d*|slow|normal|fast)?\b', cleaned)
        if speed_match:
            speed_val = speed_match.group(4)
            if speed_val:
                if speed_val == 'slow':
                    params['speed'] = 0.75
                elif speed_val == 'fast':
                    params['speed'] = 1.5
                elif speed_val == 'normal':
                    params['speed'] = 1.0
                else:
                    try:
                        params['speed'] = float(speed_val)
                    except:
                        params['speed'] = 1.5 if 'faster' in cleaned else 0.75
            else:
                params['speed'] = 1.5 if 'faster' in cleaned else 0.75
            return VoiceCommandType.SPEED, None, params
        
        # Volume command with value
        volume_match = re.search(r'\b(volume|louder|quieter|softer)\s*(up|down|to)?\s*(\d+\.?\d*|low|medium|high)?\b', cleaned)
        if volume_match:
            vol_val = volume_match.group(3)
            if vol_val:
                if vol_val == 'low':
                    params['volume'] = 0.5
                elif vol_val == 'high':
                    params['volume'] = 1.0
                elif vol_val == 'medium':
                    params['volume'] = 0.75
                else:
                    try:
                        params['volume'] = float(vol_val)
                    except:
                        params['volume'] = 1.0 if 'louder' in cleaned else 0.5
            else:
                params['volume'] = 1.0 if 'louder' in cleaned else 0.5
            return VoiceCommandType.VOLUME, None, params
        
        # Language command with language detection (v3.x: Enhanced)
        lang_match = re.search(r'\b(speak|use|change to|switch to|language)\s*(english|spanish|french|german|hindi|tamil|telugu|mandarin|chinese|italian|portuguese|japanese|korean)?\b', cleaned)
        if lang_match:
            lang_name = lang_match.group(2)
            if lang_name:
                lang_map = {
                    'english': 'en-US',
                    'spanish': 'es-ES',
                    'french': 'fr-FR',
                    'german': 'de-DE',
                    'hindi': 'hi-IN',  # v3.x
                    'tamil': 'ta-IN',  # v3.x
                    'telugu': 'te-IN',  # v3.x
                    'mandarin': 'zh-CN',  # v3.x
                    'chinese': 'zh-CN',
                    'italian': 'it-IT',
                    'portuguese': 'pt-BR',
                    'japanese': 'ja-JP',
                    'korean': 'ko-KR'
                }
                if lang_name.lower() in lang_map:
                    params['language'] = lang_map[lang_name.lower()]
            return VoiceCommandType.LANGUAGE, None, params
        
        # Check for command patterns without parameters
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, cleaned, re.IGNORECASE):
                    return cmd_type, None, None
        
        return VoiceCommandType.NONE, None, None
    
    def detect_emotion(self, transcript: str) -> EmotionType:
        """
        Detect emotion from transcript text.
        
        Args:
            transcript: The transcript text
            
        Returns:
            Detected emotion type
        """
        cleaned = transcript.lower()
        emotion_scores = {emotion: 0 for emotion in EmotionType}
        
        # Score each emotion based on patterns
        for emotion, patterns in self.emotion_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, cleaned, re.IGNORECASE))
                emotion_scores[emotion] += matches
        
        # Find emotion with highest score
        max_score = max(emotion_scores.values())
        if max_score == 0:
            return EmotionType.NEUTRAL
        
        # Return emotion with highest score
        for emotion, score in emotion_scores.items():
            if score == max_score:
                return emotion
        
        return EmotionType.NEUTRAL
    
    def correct_mis_sayings(self, transcript: str) -> str:
        """
        Correct common speech recognition mis-sayings (v3.x).
        
        Args:
            transcript: Raw transcript from speech recognition
            
        Returns:
            Corrected transcript
        """
        words = transcript.split()
        corrected_words = []
        
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            # Check if word needs correction
            corrected = False
            for correct_word, mis_sayings in self.mis_saying_corrections.items():
                if word_lower in mis_sayings:
                    # Preserve capitalization
                    if word[0].isupper():
                        corrected_words.append(correct_word.capitalize())
                    else:
                        corrected_words.append(correct_word)
                    corrected = True
                    break
            
            if not corrected:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def validate_transcript(self, transcript: str) -> Tuple[bool, Optional[str]]:
        """
        Validate and clean transcript before processing.
        Version 3.x: Enhanced with mis-saying correction.
        
        Args:
            transcript: Raw transcript from speech recognition
            
        Returns:
            Tuple of (is_valid, cleaned_transcript)
        """
        if not transcript:
            return False, None
            
        # Clean transcript
        cleaned = transcript.strip()
        
        # Version 3.x: Correct mis-sayings first
        cleaned = self.correct_mis_sayings(cleaned)
        
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
        
        # Check for voice commands - if it's ONLY a command, don't process as regular transcript
        cmd_type, _, _ = self.detect_voice_command(cleaned)
        if cmd_type != VoiceCommandType.NONE and cmd_type != VoiceCommandType.WAKE:
            # It's a command, but we still want to process it
            pass
            
        return True, cleaned
    
    def process_transcript(self, transcript: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Process a transcript and prepare it for chat API.
        Enhanced with emotion detection, command recognition, and quality metrics.
        
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
        
        # Detect voice command with parameters (v3.0.0)
        cmd_type, remaining_text, params = self.detect_voice_command(cleaned)
        
        # Handle parameter-based commands
        if params:
            if cmd_type == VoiceCommandType.SPEED and 'speed' in params:
                self.speech_speed = max(0.5, min(2.0, params['speed']))
            elif cmd_type == VoiceCommandType.VOLUME and 'volume' in params:
                self.speech_volume = max(0.0, min(1.0, params['volume']))
            elif cmd_type == VoiceCommandType.LANGUAGE and 'language' in params:
                self.language = params['language']
        
        # If it's a wake word, use remaining text; otherwise use full cleaned text
        text_to_process = remaining_text if cmd_type == VoiceCommandType.WAKE and remaining_text else cleaned
        
        # Detect emotion
        emotion = self.detect_emotion(text_to_process)
        
        # Track emotion history (v3.0.0)
        self.emotion_history.append({
            'emotion': emotion.value,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.emotion_history) > 50:
            self.emotion_history = self.emotion_history[-50:]
        
        # Detect language from metadata or text patterns (v3.0.0)
        detected_lang = metadata.get('language', self.language) if metadata else self.language
        if detected_lang and detected_lang != self.language:
            self.detected_languages.append(detected_lang)
            if len(self.detected_languages) > 10:
                self.detected_languages = self.detected_languages[-10:]
        
        # Extract confidence from metadata
        confidence = metadata.get('confidence', 0.0) if metadata else 0.0
        
        # Update audio quality metrics
        self._update_audio_quality(confidence)
        
        # Add to history
        transcript_entry = {
            'text': text_to_process,
            'original': transcript,
            'cleaned': cleaned,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'emotion': emotion.value,
            'command': cmd_type.value,
            'command_params': params,
            'confidence': confidence,
            'language': detected_lang,
            'quality_score': self._calculate_quality_score(confidence, text_to_process),
            'speech_settings': {
                'speed': self.speech_speed,
                'volume': self.speech_volume,
                'language': self.language
            }
        }
        self.transcript_history.append(transcript_entry)
        
        # Add to conversation context
        self.conversation_context.append({
            'role': 'user',
            'content': text_to_process,
            'timestamp': transcript_entry['timestamp'],
            'emotion': emotion.value,
            'command': cmd_type.value
        })
        self.conversation_turns += 1
        
        # Keep only last 50 entries
        if len(self.transcript_history) > 50:
            self.transcript_history = self.transcript_history[-50:]
        
        # Keep only last 20 conversation turns
        if len(self.conversation_context) > 20:
            self.conversation_context = self.conversation_context[-20:]
        
        return {
            'valid': True,
            'transcript': text_to_process,
            'original': transcript,
            'cleaned': cleaned,
            'confidence': confidence,
            'timestamp': transcript_entry['timestamp'],
            'emotion': emotion.value,
            'command': cmd_type.value,
            'is_command': cmd_type != VoiceCommandType.NONE,
            'quality_score': transcript_entry['quality_score'],
            'audio_quality': self._get_audio_quality_status(),
            'language': detected_lang,
            'speech_settings': {
                'speed': self.speech_speed,
                'volume': self.speech_volume,
                'language': self.language
            }
        }
    
    def _update_audio_quality(self, confidence: float):
        """Update audio quality metrics."""
        self.audio_quality_history.append({
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 measurements
        if len(self.audio_quality_history) > 100:
            self.audio_quality_history = self.audio_quality_history[-100:]
        
        # Calculate average confidence
        if self.audio_quality_history:
            self.avg_confidence = sum(m['confidence'] for m in self.audio_quality_history) / len(self.audio_quality_history)
    
    def _calculate_quality_score(self, confidence: float, text: str) -> float:
        """Calculate overall quality score for transcript."""
        # Base score from confidence
        score = confidence
        
        # Adjust based on text length (longer transcripts are often more reliable)
        length_factor = min(len(text) / 50.0, 1.0)  # Normalize to 50 chars
        score = score * 0.7 + length_factor * 0.3
        
        # Penalize very short transcripts
        if len(text) < 5:
            score *= 0.8
        
        return min(score, 1.0)
    
    def _get_audio_quality_status(self) -> str:
        """Get current audio quality status."""
        if self.avg_confidence >= 0.8:
            return 'excellent'
        elif self.avg_confidence >= 0.6:
            return 'good'
        elif self.avg_confidence >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
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
    
    def get_conversation_context(self, include_metadata: bool = False) -> List[Dict]:
        """
        Get full conversation context with metadata.
        
        Args:
            include_metadata: Whether to include emotion, command, and quality data
            
        Returns:
            List of conversation entries
        """
        if include_metadata:
            return self.conversation_context.copy()
        else:
            return [
                {'role': entry['role'], 'content': entry['content']}
                for entry in self.conversation_context
            ]
    
    def add_assistant_response(self, response: str, metadata: Optional[Dict] = None):
        """
        Add assistant response to conversation context.
        
        Args:
            response: The assistant's response text
            metadata: Optional metadata about the response
        """
        self.conversation_context.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
        self.last_response_time = datetime.now()
        
        # Keep only last 20 conversation turns
        if len(self.conversation_context) > 20:
            self.conversation_context = self.conversation_context[-20:]
    
    def get_session_stats(self) -> Dict:
        """Get session statistics. Enhanced for v3.0.0."""
        session_duration = datetime.now() - self.session_start_time
        
        # Get emotion distribution
        emotion_counts = {}
        for emotion_entry in self.emotion_history:
            emotion = emotion_entry['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return {
            'session_duration_seconds': session_duration.total_seconds(),
            'conversation_turns': self.conversation_turns,
            'transcript_count': len(self.transcript_history),
            'avg_confidence': self.avg_confidence,
            'audio_quality': self._get_audio_quality_status(),
            'last_response_time': self.last_response_time.isoformat() if self.last_response_time else None,
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            # Version 3.0.0 additions
            'language': self.language,
            'detected_languages': list(set(self.detected_languages[-5:])),  # Last 5 unique
            'speech_settings': {
                'speed': self.speech_speed,
                'volume': self.speech_volume
            },
            'interruptions': self.interruptions,
            'emotion_distribution': emotion_counts,
            'adaptive_sensitivity': self.adaptive_sensitivity,
            'total_summaries': len(self.conversation_summaries)
        }
    
    def record_speech_segment(self, start: bool = True):
        """
        Record voice activity detection segment.
        
        Args:
            start: True if speech started, False if it ended
        """
        now = datetime.now()
        
        if start:
            self.current_speech_start = now
        else:
            if self.current_speech_start:
                duration = (now - self.current_speech_start).total_seconds()
                self.speech_segments.append({
                    'start': self.current_speech_start.isoformat(),
                    'end': now.isoformat(),
                    'duration': duration
                })
                self.current_speech_start = None
                
                # Keep only last 100 segments
                if len(self.speech_segments) > 100:
                    self.speech_segments = self.speech_segments[-100:]
    
    def record_interruption(self):
        """Record a user interruption (v3.0.0)."""
        self.interruptions += 1
    
    def generate_conversation_summary(self, max_turns: int = 10) -> Dict:
        """
        Generate a summary of the conversation (v3.0.0).
        
        Args:
            max_turns: Maximum number of turns to include in summary
            
        Returns:
            Dictionary with conversation summary
        """
        recent_context = self.conversation_context[-max_turns:] if len(self.conversation_context) > max_turns else self.conversation_context
        
        user_messages = [entry for entry in recent_context if entry.get('role') == 'user']
        assistant_messages = [entry for entry in recent_context if entry.get('role') == 'assistant']
        
        # Analyze emotions
        emotions = [entry.get('emotion', 'neutral') for entry in user_messages if entry.get('emotion')]
        dominant_emotion = max(set(emotions), key=emotions.count) if emotions else 'neutral'
        
        # Calculate statistics
        total_words = sum(len(entry.get('content', '').split()) for entry in recent_context)
        avg_message_length = total_words / len(recent_context) if recent_context else 0
        
        summary = {
            'session_id': self.session_start_time.isoformat(),
            'total_turns': len(recent_context),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'dominant_emotion': dominant_emotion,
            'avg_message_length': round(avg_message_length, 1),
            'interruptions': self.interruptions,
            'duration_seconds': (datetime.now() - self.session_start_time).total_seconds(),
            'topics': self._extract_topics(recent_context),
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversation_summaries.append(summary)
        if len(self.conversation_summaries) > 20:
            self.conversation_summaries = self.conversation_summaries[-20:]
        
        return summary
    
    def _extract_topics(self, context: List[Dict]) -> List[str]:
        """Extract main topics from conversation."""
        # Simple keyword extraction based on common question words and important terms
        topics = []
        all_text = ' '.join([entry.get('content', '') for entry in context]).lower()
        
        topic_keywords = {
            'weather': r'\b(weather|temperature|rain|snow|sunny|cloudy)\b',
            'time': r'\b(time|clock|hour|minute|today|tomorrow|date)\b',
            'question': r'\b(what|why|how|when|where|who|which|explain|tell me)\b',
            'help': r'\b(help|assist|support|guide|how to|tutorial)\b',
            'information': r'\b(information|info|details|facts|data|knowledge)\b',
            'calculation': r'\b(calculate|math|number|plus|minus|multiply|divide)\b'
        }
        
        for topic, pattern in topic_keywords.items():
            if re.search(pattern, all_text):
                topics.append(topic)
        
        return topics[:5]  # Return top 5 topics
    
    def adapt_sensitivity(self, audio_levels: List[float]):
        """
        Adapt listening sensitivity based on audio environment (v3.0.0).
        
        Args:
            audio_levels: Recent audio level measurements
        """
        if not audio_levels or len(audio_levels) < 10:
            return
        
        avg_level = sum(audio_levels) / len(audio_levels)
        max_level = max(audio_levels)
        
        # Adjust threshold based on environment
        if avg_level < 0.01:
            # Very quiet environment - lower threshold
            self.adaptive_sensitivity = max(0.005, self.adaptive_sensitivity * 0.9)
        elif avg_level > 0.1:
            # Noisy environment - raise threshold
            self.adaptive_sensitivity = min(0.05, self.adaptive_sensitivity * 1.1)
        
        # Update base threshold
        self.audio_level_threshold = self.adaptive_sensitivity
    
    def get_emotion_based_response_guidance(self) -> Dict:
        """
        Get response guidance based on detected emotions (v3.0.0).
        
        Returns:
            Dictionary with response style guidance
        """
        if not self.emotion_history:
            return {'tone': 'neutral', 'speed': 1.0, 'empathy': 'normal'}
        
        recent_emotions = [e['emotion'] for e in self.emotion_history[-5:]]
        dominant_emotion = max(set(recent_emotions), key=recent_emotions.count)
        
        guidance_map = {
            'happy': {'tone': 'enthusiastic', 'speed': 1.1, 'empathy': 'high'},
            'excited': {'tone': 'energetic', 'speed': 1.2, 'empathy': 'high'},
            'sad': {'tone': 'compassionate', 'speed': 0.9, 'empathy': 'very_high'},
            'angry': {'tone': 'calm', 'speed': 0.95, 'empathy': 'very_high'},
            'frustrated': {'tone': 'patient', 'speed': 0.9, 'empathy': 'high'},
            'questioning': {'tone': 'clear', 'speed': 1.0, 'empathy': 'normal'},
            'calm': {'tone': 'gentle', 'speed': 1.0, 'empathy': 'normal'},
            'neutral': {'tone': 'neutral', 'speed': 1.0, 'empathy': 'normal'}
        }
        
        return guidance_map.get(dominant_emotion, guidance_map['neutral'])
    
    def reset(self):
        """Reset handler state."""
        self.is_active = False
        self.is_paused = False
        self.current_transcript = ""
        self.transcript_history = []
        self.conversation_context = []
        self.audio_quality_history = []
        self.avg_confidence = 0.0
        self.conversation_turns = 0
        self.last_response_time = None
        self.session_start_time = datetime.now()
        self.speech_segments = []
        self.current_speech_start = None
        # Version 3.0.0: Reset new features (but keep preferences)
        self.detected_languages = []
        self.adaptive_sensitivity = 0.01
        self.interruptions = 0
        self.emotion_history = []
        # Don't reset: language, speech_speed, speech_volume (user preferences)
    
    def set_active(self, active: bool):
        """Set active state."""
        self.is_active = active
        if not active:
            self.current_transcript = ""
        else:
            # Reset session start time when activating
            self.session_start_time = datetime.now()
    
    def set_paused(self, paused: bool):
        """Set paused state."""
        self.is_paused = paused
        if paused and self.current_speech_start:
            # End current speech segment if paused
            self.record_speech_segment(start=False)
    
    def get_voice_command_help(self) -> str:
        """Get help text for voice commands. Enhanced for v3.0.0."""
        return """Voice Commands:
• "Hey Poseidon" or "Poseidon" - Wake word to activate
• "Pause" or "Stop listening" - Pause voice recognition
• "Resume" or "Continue" - Resume voice recognition
• "Stop" or "Exit" - End voice session
• "Repeat" or "Say that again" - Repeat last response
• "Clear" or "Reset" - Clear conversation history
• "Help" - Show this help message

Version 3.0.0 New Commands:
• "Faster" or "Slower" - Adjust speech speed
• "Louder" or "Quieter" - Adjust volume
• "Speak English/Spanish/French" - Change language
• "Settings" - Show current settings"""


# Global instance
_voice_handler: Optional[PoseidonVoiceHandler] = None


def get_voice_handler() -> PoseidonVoiceHandler:
    """Get or create global voice handler instance."""
    global _voice_handler
    if _voice_handler is None:
        _voice_handler = PoseidonVoiceHandler()
    return _voice_handler
