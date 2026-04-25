"""
services/ocr.py — Delivery photo OCR pipeline.

Flow:
  User sends photo → extract_text_from_image() → raw text
  → Z.ai interprets → calls update_inventory() automatically

Uses EasyOCR (local, no API key, supports English + Malay).
Models download on first run (~100MB, cached after that).

Owner: Person 1
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Lazy-loaded — only initialised when first photo arrives
_reader = None
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ocr")


def _load_reader():
    """Load EasyOCR model (blocking — run in executor)."""
    global _reader
    if _reader is None:
        import easyocr
        logger.info("Loading EasyOCR model (first run ~30s, cached after)...")
        _reader = easyocr.Reader(["en", "ms"], gpu=False, verbose=False)
        logger.info("EasyOCR ready.")
    return _reader


def _run_ocr(image_bytes: bytes) -> str:
    """Run OCR synchronously (called in thread executor)."""
    reader = _load_reader()
    # detail=0 → text only, paragraph=True → merge nearby text blocks
    results = reader.readtext(image_bytes, detail=0, paragraph=True)
    return " | ".join(str(r).strip() for r in results if str(r).strip())


async def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Async wrapper — runs OCR in a thread so it doesn't block the event loop.

    Returns:
        Raw extracted text, pipe-separated blocks. Empty string if OCR fails.
    """
    loop = asyncio.get_event_loop()
    try:
        text = await loop.run_in_executor(_executor, _run_ocr, image_bytes)
        logger.info(f"OCR extracted {len(text)} chars: {text[:80]}...")
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""
