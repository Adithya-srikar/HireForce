"""
TTS Service – edge-tts (Microsoft Neural, ~300ms, no model files needed).

Falls back to a silent stub if edge-tts is not installed.
Streams audio as MP3 bytes, chunked per sentence for low perceived latency.
"""
import asyncio
import logging
import re
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# High-quality, neutral, English neural voice
AI_VOICE = "en-US-AriaNeural"

# Sentence boundary split (greedy — keep short bursts flowing fast)
_SENT_RE = re.compile(r'(?<=[.!?])\s+')


def split_sentences(text: str) -> list[str]:
    """Split text into sentences for streaming TTS."""
    parts = _SENT_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


async def stream_sentence(text: str) -> bytes:
    """
    Synthesise a single sentence and return full MP3 bytes.
    Uses edge-tts which streams internally; we collect and return.
    """
    try:
        import edge_tts
        chunks: list[bytes] = []
        communicate = edge_tts.Communicate(text, AI_VOICE)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)
    except ImportError:
        logger.warning("edge-tts not installed – returning empty audio")
        return b""
    except Exception as e:
        logger.error(f"TTS error for text '{text[:40]}…': {e}")
        return b""


async def stream_tts(text: str) -> AsyncIterator[bytes]:
    """
    Async generator: yields MP3 bytes for each sentence in `text`.
    The caller sends each chunk over the WebSocket as soon as it's ready,
    so the user hears the first sentence while later ones are still synthesising.
    """
    sentences = split_sentences(text)
    if not sentences:
        return

    for sentence in sentences:
        audio = await stream_sentence(sentence)
        if audio:
            yield audio
