"""
Whisper Integration for High-Quality Speech Recognition.
Replaces custom speech recognition with OpenAI Whisper for better accuracy.
"""
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try to import Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Install with: pip install openai-whisper")

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


class WhisperTranscriber:
    """
    High-quality speech-to-text using OpenAI Whisper.
    Supports both standard Whisper and faster-whisper for better performance.
    """
    
    def __init__(self, model_size: str = "base", use_faster: bool = True, device: Optional[str] = None):
        """
        Initialize Whisper transcriber.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            use_faster: Use faster-whisper if available (faster and more efficient)
            device: Device to use ("cpu", "cuda", "auto")
        """
        self.model_size = model_size
        self.use_faster = use_faster and FASTER_WHISPER_AVAILABLE
        self.model = None
        self.device = device or ("cuda" if os.environ.get("CUDA_AVAILABLE") == "1" else "cpu")
        
        if not WHISPER_AVAILABLE and not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "Whisper not available. Install with:\n"
                "  pip install openai-whisper\n"
                "  or\n"
                "  pip install faster-whisper"
            )
        
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model."""
        try:
            if self.use_faster:
                logger.info(f"Loading faster-whisper model: {self.model_size}")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type="float16" if self.device == "cuda" else "int8"
                )
                logger.info("Faster-whisper model loaded successfully")
            else:
                logger.info(f"Loading OpenAI Whisper model: {self.model_size}")
                self.model = whisper.load_model(self.model_size, device=self.device)
                logger.info("OpenAI Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (None = auto-detect)
            task: "transcribe" or "translate"
            **kwargs: Additional Whisper parameters
            
        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        try:
            if self.use_faster:
                # Use faster-whisper API
                segments, info = self.model.transcribe(
                    audio_path,
                    language=language,
                    task=task,
                    **kwargs
                )
                
                # Collect segments
                text_segments = []
                full_text = ""
                
                for segment in segments:
                    text_segments.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text
                    })
                    full_text += segment.text + " "
                
                return {
                    "text": full_text.strip(),
                    "language": info.language,
                    "language_probability": info.language_probability,
                    "segments": text_segments,
                    "duration": info.duration
                }
            else:
                # Use standard Whisper API
                result = self.model.transcribe(
                    audio_path,
                    language=language,
                    task=task,
                    **kwargs
                )
                
                return {
                    "text": result["text"],
                    "language": result.get("language", "unknown"),
                    "segments": result.get("segments", []),
                    "duration": sum(seg.get("end", 0) - seg.get("start", 0) for seg in result.get("segments", []))
                }
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    def transcribe_audio_data(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio data directly (without saving to file).
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (None = auto-detect)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with transcription results
        """
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            result = self.transcribe(tmp_path, language=language, **kwargs)
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
        
        return result
    
    def detect_language(self, audio_path: str) -> Dict[str, Any]:
        """
        Detect language of audio without full transcription.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with language detection results
        """
        if self.use_faster:
            _, info = self.model.transcribe(audio_path, beam_size=1)
            return {
                "language": info.language,
                "probability": info.language_probability
            }
        else:
            # Standard Whisper doesn't have separate language detection
            # Do a quick transcription with language=None
            result = self.transcribe(audio_path, language=None)
            return {
                "language": result.get("language", "unknown"),
                "probability": 1.0  # Standard Whisper doesn't provide probability
            }


def get_whisper_transcriber(
    model_size: str = "base",
    use_faster: bool = True
) -> Optional[WhisperTranscriber]:
    """
    Get or create a Whisper transcriber instance.
    
    Returns None if Whisper is not available.
    """
    if not WHISPER_AVAILABLE and not FASTER_WHISPER_AVAILABLE:
        logger.warning("Whisper not available, returning None")
        return None
    
    try:
        return WhisperTranscriber(model_size=model_size, use_faster=use_faster)
    except Exception as e:
        logger.error(f"Error creating Whisper transcriber: {e}")
        return None

