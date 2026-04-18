"""
STT Service – faster-whisper with GPU auto-detection.
Model is loaded once and reused (singleton).
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)
_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"

    compute = "float16" if device == "cuda" else "int8"
    logger.info(f"Loading faster-whisper (small, {device}, {compute})…")

    from faster_whisper import WhisperModel
    _model = WhisperModel("small", device=device, compute_type=compute)
    logger.info("Whisper model ready.")
    return _model


async def transcribe_pcm(pcm_bytes: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribe raw 16-bit signed mono PCM audio bytes.
    Returns the transcribed text (empty string if nothing detected).
    """
    if not pcm_bytes:
        return ""

    model = _load_model()

    # Convert int16 PCM → float32 normalised to [-1, 1]
    audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    segments, _ = model.transcribe(
        audio,
        beam_size=1,           # fastest decoding
        language="en",
        vad_filter=True,       # built-in silero-VAD to skip silence
        vad_parameters={"min_silence_duration_ms": 300},
    )
    return " ".join(seg.text.strip() for seg in segments).strip()


def warm_up():
    """Call at startup to load the model before the first request."""
    _load_model()
