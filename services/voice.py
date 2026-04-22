"""
services/voice.py — Voice note transcription using faster-whisper.

Handles Telegram OGG voice notes → text transcript.
Owner: Person 3

Requirements:
    pip install faster-whisper
    System: ffmpeg must be installed (brew install ffmpeg / apt install ffmpeg)

Model: 'tiny' loads in ~1 second, good enough for short Malay/English voice notes.
       Switch to 'base' if accuracy needs improvement.
"""
import io
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_model():
    """Lazy-load the Whisper model on first use."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Loading Whisper tiny model...")
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("Whisper model loaded.")
        except ImportError:
            logger.error("faster-whisper not installed. Run: pip install faster-whisper")
            raise
    return _whisper_model


async def transcribe_voice(file_bytes: bytes, language_hint: str = None) -> str:
    """
    Transcribe a Telegram voice note (OGG/Opus) to text.

    Args:
        file_bytes:    Raw bytes of the OGG file downloaded from Telegram.
        language_hint: Optional ISO language code ('ms', 'zh', 'en').
                       If None, Whisper auto-detects.

    Returns:
        Transcript string, or empty string on failure.
    """
    if not file_bytes:
        return ""

    try:
        model = _get_model()
    except Exception as e:
        logger.error(f"Whisper model unavailable: {e}")
        return ""

    # Write to a temp file — faster-whisper needs a file path, not bytes
    try:
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        transcribe_kwargs = {
            "beam_size": 5,
            "vad_filter": True,       # removes silence
            "vad_parameters": {"min_silence_duration_ms": 500},
        }
        if language_hint:
            transcribe_kwargs["language"] = language_hint

        segments, info = model.transcribe(tmp_path, **transcribe_kwargs)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()

        detected = info.language if hasattr(info, "language") else "unknown"
        logger.info(f"Transcribed voice note | lang={detected} | chars={len(transcript)}")

        return transcript

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""

    finally:
        # Always clean up the temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
